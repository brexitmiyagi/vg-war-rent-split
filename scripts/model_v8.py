"""v8 valuation: the single source of truth for every number in the v8 piece.

Same structure as model_v7.py (kept as legacy). What changed, and why:
1. Curve: CME settlements of 7 Oct 2026 (common.CURVE_FILE), ECB EUR/USD of 7 Oct (1.1177).
2. Fee escalation. Venture Global's own convention for "total contracted revenue" (IPO prospectus,
   424B4, 24 Jan 2025): "17.5% of the fixed facility charge component increases by 2.5% annual
   inflation every year following the first full year after COD". That is the company's illustrative
   assumption, not a disclosed SPA term; I use it as stated. First escalation year (ASSUMPTION, from
   CODs in data/vg_contracts.csv): Calcasieu 2027 (COD Apr 2025), Plaquemines Phase 1 2028 (COD Q4
   2026), Plaquemines Phase 2 2029 (COD mid-2027), CP2 Phase 1 2031 and Phase 2 2032 (COD 2029/2030),
   CP2 split 50/50. Escalation applies to the long-term book (1,560 TBtu Calcasieu + Plaquemines, and
   CP2 volume above that from 2030). The 2032-2049 contracted cash is now summed year by year.
3. Costs stay flat in nominal terms in the central case (as in v7). Sensitivity: costs rise 2.5% a
   year from 2027, which offsets most of the escalation.
4. Interest, calibrated to the Q2 2026 10-Q (Note 8 interest table; 30 Jun net debt 37.8bn):
   cash interest = (stated 691 + other fees 46 - interest income 26) x 4 / 37,796 = 7.52% of net debt
   (v7 used an assumed 6.3%); P&L interest cost before capitalization adds amortization of discounts
   (67): (804 - 26) x 4 / 37,796 = 8.23%.
5. Capitalized interest (EPS and cash tax only; cash and value unaffected): Q2 2026 capitalized 315m
   (1.26bn a year), mostly CP2 now that part of Plaquemines is in service. ASSUMPTION: 1.4bn in 2027
   as CP2 draws more debt, 1.1bn in 2028, 0.6bn in 2029, 0.2bn in 2030, none in 2031 as phases are
   placed in service. For cash tax I assume the same amounts are capitalized (IRC s.263A(f)).
"""
import os, io, csv, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import valuation as V
    import sotp as S
from common import RESULTS, PRICE_KEY

PX = V.bs[PRICE_KEY]
YEARS = list(V.YEARS)
JK = S.jk
FUT = {y: JK[y] for y in YEARS}
C26 = V.COST
BASIS26 = (110 + 325) / 1000
C_EX = (C26 * V.vol[2026] - BASIS26 * 1000) / V.vol[2026]
BASIS = {2027: BASIS26, 2028: BASIS26 / 2, 2029: 0.0, 2030: 0.0, 2031: 0.0}
CP2X = 0.40
L_CENTRAL = 3.50
BOLT_TBTU = {2027: 0.0, 2028: 10 * 0.1 * 52, 2029: (10 * 0.75 + 6.4 * 0.5) * 52, 2030: 16.4 * 52, 2031: 16.4 * 52}
BOLT_CAPEX = {2027: 4.0, 2028: 4.0, 2029: 2.7, 2030: 0.0, 2031: 0.0}
DIV = 0.04 * 4 * 2.498
BASE_BOOK = 1560                                  # TBtu: Calcasieu 10 + Plaquemines 20 MTPA third-party SPAs
ESC_SHARE, ESC_RATE = 0.175, 0.025                # company convention (424B4)
BASE_TRANCHES = ((10.0, 2027), (13.3, 2028), (6.7, 2029))   # (MTPA, first escalation year)
CP2_TRANCHES = ((0.5, 2031), (0.5, 2032))
ND30 = V.nd30jun
CASH_RATE = (691 + 46 - 26) * 4 / 37796           # 7.52%
PL_RATE = (804 - 26) * 4 / 37796                  # 8.23%
CAPI = {2027: 1.4, 2028: 1.1, 2029: 0.6, 2030: 0.2, 2031: 0.0}   # ASSUMPTION, $bn
h2_ebitda = (V.bs["ebitda_guide_2026_low"] + V.bs["ebitda_guide_2026_high"]) / 2000 - V.bs["h1_2026_adjusted_ebitda"] / 1000
h2_capex = (V.bs["capex_2026_guide"] - V.bs["capex_h1_2026"]) / 1000
ND0 = ND30 + h2_capex - (h2_ebitda - ND30 * CASH_RATE / 2 - 0.4)
RUNOFF = 2049

def esc(y, first):
    """Multiplier on the fixed fee: 17.5% of it grows 2.5% a year from its first escalation year."""
    return 1.0 + ESC_SHARE * ((1 + ESC_RATE) ** max(0, y - first + 1) - 1)

def m_base(y, on=True):
    if not on: return 1.0
    return sum(w * esc(y, f) for w, f in BASE_TRANCHES) / sum(w for w, _ in BASE_TRANCHES)

def m_cp2(y, on=True):
    if not on: return 1.0
    return sum(w * esc(y, f) for w, f in CP2_TRANCHES)

def unit_cost(y, base, cost_infl):
    return base * (1 + cost_infl) ** max(0, y - 2026)

def contracted_rev(y, con, fee, cp2x, on):
    base = min(con, BASE_BOOK); extra = max(0.0, con - BASE_BOOK)
    if y >= 2030:
        return (base * fee * m_base(y, on) + extra * (fee + cp2x) * m_cp2(y, on)) / 1000
    return (base * fee * m_base(y, on) + extra * fee) / 1000

def series(L, cost_mode="central", bolt=True, cp2x=CP2X, flat_cost=None, escal=True, cost_infl=0.0):
    vol = dict(V.vol); op = dict(V.open_tbtu); capex = dict(V.CAPEX)
    if not bolt:
        for y in YEARS:
            vol[y] -= BOLT_TBTU[y]; op[y] = max(0.0, op[y] - BOLT_TBTU[y]); capex[y] -= BOLT_CAPEX[y]
    c_unit0 = flat_cost if flat_cost is not None else (C26 if cost_mode == "calibrated" else C_EX)
    def cost(y):
        c = unit_cost(y, c_unit0, cost_infl) * vol[y] / 1000
        if flat_cost is None and cost_mode == "central":
            c += BASIS[y]
        return c
    rows = {}
    for y in YEARS:
        con = vol[y] - op[y]
        rev_c = contracted_rev(y, con, V.CONTRACT_FEE[y], cp2x, escal)
        rev_o = op[y] * FUT[y] / 1000
        c = cost(y)
        rows[y] = dict(vol=vol[y], open=op[y], con=con, ebitda=rev_c + rev_o - c, ec=rev_c - c * con / vol[y],
                       eo=rev_o - c * op[y] / vol[y], capex=capex[y], rev_c=rev_c)
    # 2032-2049, year by year; 2050 on as a perpetuity at 2049 costs
    y0 = 2031; con = vol[y0] - op[y0]; share_c = con / vol[y0]
    tail = []
    for y in range(2032, RUNOFF + 1):
        cu = unit_cost(y, c_unit0, cost_infl)
        ec = contracted_rev(y, con, 2.45, cp2x, escal) - con * cu / 1000 - 1.0 * share_c
        eo = op[y0] * (L - cu) / 1000 - 1.0 * (1 - share_c)
        tail.append((y, ec, eo))
    cu49 = unit_cost(RUNOFF, c_unit0, cost_infl)
    term = dict(con=con, open=op[y0], share_c=share_c, tail=tail,
                eo_perp=op[y0] * (L - cu49) / 1000 - 1.0 * (1 - share_c), conv=con * (L - cu49) / 1000)
    return rows, term

def net_debt_path(rows, nd0=None):
    nd = ND0 if nd0 is None else nd0; out = {}
    for i, y in enumerate(YEARS):
        e = rows[y]["ebitda"]; cash_int = nd * CASH_RATE
        cash_tax = V.TAX * max(0.0, e - (cash_int - CAPI[y]) - (1.0 + 0.3 * i))
        fcf = e - cash_int - cash_tax - rows[y]["capex"] - V.PREF - V.NCI - DIV
        pl_int = nd * PL_RATE - CAPI[y]
        nd -= fcf; out[y] = dict(nd=nd, fcf=fcf, cash_int=cash_int, pl_int=pl_int, cash_tax=cash_tax)
    return out

def value(L, cost_mode="central", bolt=True, cp2x=CP2X, roll=False, rc=S.RC, ro=S.RO, flat_cost=None, uplift=0.0, escal=True, cost_infl=0.0):
    rows, term = series(L, cost_mode, bolt, cp2x, flat_cost, escal, cost_infl)
    base_year = 2028 if roll else 2026
    yrs = [2029, 2030, 2031] if roll else YEARS
    pv = 0.0
    for y in yrs:
        t = y - base_year; r = rows[y]
        ec = r["ec"] + (uplift if y >= 2029 else 0.0)
        pv += (ec * (1 - V.TAX) + V.TAX * S.DA[y]) / (1 + rc) ** t + r["eo"] * (1 - V.TAX) / (1 + ro) ** t - r["capex"] / (1 + rc) ** t
    for y, ec, eo in term["tail"]:
        t = y - base_year
        pv += ((ec + uplift) * (1 - V.TAX) + V.TAX * 2.6) / (1 + rc) ** t + eo * (1 - V.TAX) / (1 + ro) ** t
    tN = RUNOFF - base_year
    pv += term["eo_perp"] * (1 - V.TAX) / ro / (1 + ro) ** tN
    pv += term["conv"] * (1 - V.TAX) / ro / (1 + ro) ** tN
    nci = V.NCI * (1 - V.TAX) / rc
    nd = net_debt_path(rows)[2028]["nd"] if roll else ND0
    return (pv - nd - S.PREF_LIQ - nci - S.BP) / V.SHARES

def needed(**kw):
    lo, hi = -5.0, 30.0
    for _ in range(80):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if value(m, **kw) < PX else (lo, m)
    return m

def ke(v0, v28):
    return ((v28 + 2 * 0.16) / v0) ** (1 / 2.23) - 1

if __name__ == "__main__":
    L_ = []
    L_.append(f"price {PX} (Oct 7 close); CME futures fees (Oct 7 settlements) 2027-31: " + ", ".join(f"{y} {FUT[y]:.2f}" for y in YEARS))
    L_.append(f"cost: 2026 calibrated {C26:.3f}/MMBtu; underlying ex-basis {C_EX:.3f}/MMBtu; Plaquemines basis {BASIS26:.3f}bn in 2026-27, half in 2028, zero from 2029")
    L_.append(f"interest (Q2 2026 10-Q): cash {CASH_RATE:.2%} of net debt, P&L before capitalization {PL_RATE:.2%}; net debt end-2026 {ND0:.2f}bn (30 Jun {ND30:.2f})")
    L_.append("escalation multiplier on the fixed fee (base book | CP2): " + ", ".join(f"{y} {m_base(y):.3f}|{m_cp2(y):.3f}" for y in (2027, 2028, 2029, 2030, 2031, 2035, 2040, 2049)))
    v0 = value(L_CENTRAL); v28 = value(L_CENTRAL, roll=True)
    L_.append(f"CENTRAL (futures to 2031, then {L_CENTRAL:.2f}; escalation on; costs flat; bolt-ons in; CP2 +{CP2X}): today {v0:.2f}, end-2028 {v28:.2f}, implied equity return {ke(v0, v28):.1%} a year incl. dividends")
    L_.append(f"  fee the price needs from 2032 (futures kept to 2031): {needed():.2f}")
    sens = (("no escalation (v7 basis)", dict(escal=False)),
            ("escalation + costs +2.5%/yr", dict(cost_infl=0.025)),
            ("calibrated costs", dict(cost_mode="calibrated")),
            ("ex bolt-ons", dict(bolt=False)),
            ("CP2 +0.00", dict(cp2x=0.0)),
            ("CP2 +0.85", dict(cp2x=0.85)))
    sens_out = []
    for lab, kw in sens:
        a, b, c = value(L_CENTRAL, **kw), value(L_CENTRAL, roll=True, **kw), needed(**kw)
        sens_out.append((lab, a, b, c))
        L_.append(f"  {lab:<30} today {a:6.2f}  end-2028 {b:6.2f}  needs {c:5.2f}")
    L_.append("long-run fee from 2032 -> value today (central) | end-2028 | today, costs +2.5%/yr | today ex bolt-ons")
    pay = []
    for x in [i / 2 for i in range(0, 17)]:
        r = (x, value(x), value(x, roll=True), value(x, cost_infl=0.025), value(x, bolt=False))
        pay.append(r); L_.append("  {:4.1f}  {:7.2f}  {:7.2f}  {:7.2f}  {:7.2f}".format(*r))
    slope = (value(4.5) - value(2.5)) / 2
    L_.append(f"each $1 of long-run fee from 2032 is worth {slope:.2f} a share today ({slope / PX:.0%} of price)")
    hh = value(L_CENTRAL) - value(L_CENTRAL - 1.15)
    L_.append(f"Henry Hub +$1 for good (JKM unchanged) ~ -1.15 on the long-run fee: {-hh:.2f} a share (long-run only; 2027-31 futures held)")
    costs = [1.15, 0.92, 0.75, 0.60]
    Ls = [2.5, 3.0, 3.5, 4.0, 4.5, 5.19, 6.0]
    L_.append("grid: value today by long-run fee (rows) and flat cost per MMBtu (columns " + ", ".join(f"{c:.2f}" for c in costs) + "), escalation on")
    grid = []
    for l in Ls:
        g = [value(l, flat_cost=c) for c in costs]; grid.append([l] + g)
        L_.append(f"  {l:4.2f}  " + "  ".join(f"{v:7.2f}" for v in g))
    L_.append(f"cost: what 0.92 vs 1.15 flat is worth at {L_CENTRAL}: {value(L_CENTRAL, flat_cost=0.92) - value(L_CENTRAL, flat_cost=1.15):.2f} a share")
    rows, _ = series(3.0)
    op29 = rows[2029]["open"]
    mine3 = rows[2029]["ebitda"] - op29 * (FUT[2029] - 3.0) / 1000
    L_.append(f"2029 EBITDA at a $3 open fee, central costs, Aug volumes: {mine3:.2f}bn (management, March: about 11; $5 -> 17)")
    extra = (3000 - op29) * (3.0 - C_EX) / 1000
    L_.append(f"  March framework implies 3000 TBtu of 2029 open volume ($3.0bn per $1); May deck 1,850; Aug deck 2,475. Extra ~{3000 - op29:.0f} TBtu worth ~{extra:.2f}bn at $3; remaining gap {11.0 - mine3 - extra:.2f}bn")
    gap = 11.0 - mine3
    L_.append(f"  if management's 11bn is right (gap {gap:.2f}bn added from 2029): today {value(L_CENTRAL, uplift=gap):.2f}, needs {needed(uplift=gap):.2f}")
    rows, _ = series(L_CENTRAL); nd = net_debt_path(rows)
    from eps_path import DA as DA_
    L_.append("central path: year, EBITDA, capitalized interest, P&L interest, EPS, FCF after dividends, net debt, ND/EBITDA")
    eps_rows = []
    e26 = (V.bs["ebitda_guide_2026_low"] + V.bs["ebitda_guide_2026_high"]) / 2000
    int26 = (933 + 2 * 489) / 1000      # H1 2026 interest expense, net of capitalization (10-Q) + H2 at the Q2 run-rate
    ebt26 = e26 - DA_[2026] - int26; eps26 = (ebt26 * (1 - V.TAX) - V.PREF - V.NCI) / V.SHARES
    eps_rows.append((2026, e26, 1.19, int26, eps26, float("nan"), float("nan"), ND0))
    L_.append(f"  2026  {e26:6.2f}  ~1.19 (H1 0.595 x 2)  {int26:5.2f}  {eps26:5.2f} (guidance midpoint EBITDA; reported interest)  net debt end-2026 {ND0:5.1f}")
    for y in YEARS:
        e = rows[y]["ebitda"]; d = nd[y]
        ebt = e - DA_[y] - d["pl_int"]; ni = ebt - V.TAX * max(0, ebt) - V.PREF - V.NCI
        eps = ni / V.SHARES
        ebt0 = e - DA_[y] - (d["pl_int"] + CAPI[y]); eps0 = (ebt0 - V.TAX * max(0, ebt0) - V.PREF - V.NCI) / V.SHARES
        eps_rows.append((y, e, CAPI[y], d["pl_int"], eps, eps0, d["fcf"], d["nd"]))
        L_.append(f"  {y}  {e:6.2f}  {CAPI[y]:4.2f}  {d['pl_int']:5.2f}  {eps:5.2f} (no capitalization {eps0:5.2f})  {d['fcf']:6.2f}  {d['nd']:5.1f}  {d['nd'] / e:4.1f}x")
    for y in (2030, 2031):
        e = rows[y]["ebitda"]; ndy = nd[y]["nd"]
        for m, lab in ((8.1, "VG"), (10.3, "Cheniere")):
            eq = (m * e - ndy - S.PREF_LIQ - V.NCI * (1 - V.TAX) / S.RC - S.BP) / V.SHARES
            L_.append(f"  multiple check {y} at {lab} {m}x: {eq:.2f}/share in {y}, {eq / 1.12 ** (y - 2026.8):.2f} today at 12%")
    out = "\n".join(L_); print(out)
    open(os.path.join(RESULTS, "model_v8.txt"), "w").write(out + "\n")
    with open(os.path.join(RESULTS, "payoff_v8.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["long_run_fee_from_2032", "today_central", "end2028_central", "today_costs_inflating", "today_ex_boltons"])
        for r in pay: w.writerow([f"{x:.2f}" for x in r])
    with open(os.path.join(RESULTS, "grid_v8.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["long_run_fee"] + [f"cost_{c:.2f}" for c in costs])
        for r in grid: w.writerow([f"{x:.2f}" for x in r])
    with open(os.path.join(RESULTS, "eps_path_v8.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["year", "ebitda_bn", "capitalized_interest_bn", "pl_interest_bn", "eps", "eps_without_capitalization", "fcf_after_div_bn", "net_debt_bn"])
        for r in eps_rows: w.writerow([r[0]] + [f"{x:.2f}" for x in r[1:]])
