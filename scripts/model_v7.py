"""LEGACY (v7). Superseded by model_v8.py, which adds fee escalation, capitalized interest, interest
calibrated to the Q2 2026 10-Q and the 7 Oct CME curve. Kept so the v7 numbers can be reproduced
(set CURVE_FILE back to cme_settlements_2026-10-06.csv and EURUSD to 1.1269 in common.py).

v7 valuation: the single source of truth for every number in the v7 piece.

Changes from v6 (valuation_v6.py, kept as legacy):
1. Fee path: CME futures (JKM method, Oct 6) for every year they exist, 2027-2031, then a stated
   long-run fee from 2032. Central long-run fee 3.50 (ASSUMPTION): the top of the contract-market
   anchors (Cheniere's 2.50-3.00 planning margin, Vitol ~3.00 per traders, Sabel's mid-term deal
   'north of a $3 net spread') and the bottom of Sabel's own replacement-cost range for long-term
   contracts ($3.50-4.50). Shown against a grid of long-run fees and costs.
2. Costs: 2026 calibration split into an underlying cost per MMBtu and the Plaquemines basis
   cost (110m in Q1 per the Q4 2025 deck, 300-350m for Q2-Q4 per the Q1 2026 deck), which the
   company says declines in 2028. ASSUMPTION: basis 0.435bn in 2027, half in 2028, none after.
   Temporary power isn't quantified anywhere, so it stays in.
3. Bolt-ons: the company's 2028-31 volumes include the CP2 bolt-on (10 MTPA, first production
   late 2028) and the Plaquemines bolt-on (6.4 MTPA, 2029), neither at FID. A switch removes their
   volume and an ASSUMED capex of $650 a tonne.
4. Implied equity return between today's value and the end-2028 value is printed.
"""
import os, io, csv, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import valuation as V
    import sotp as S
from common import RESULTS, PRICE_KEY

PX = V.bs[PRICE_KEY]
YEARS = list(V.YEARS)
JK = S.jk                                   # CME JKM-method fees by year
FUT = {y: JK[y] for y in YEARS}             # 2027-2031 futures
C26 = V.COST                                # 2026 all-in cost per MMBtu (calibrated)
BASIS26 = (110 + 325) / 1000                # $bn, Plaquemines basis in 2026
C_EX = (C26 * V.vol[2026] - BASIS26 * 1000) / V.vol[2026]   # underlying cost per MMBtu ex basis
BASIS = {2027: BASIS26, 2028: BASIS26 / 2, 2029: 0.0, 2030: 0.0, 2031: 0.0}
CP2X = 0.40                                 # CP2 contract fee above Calcasieu's (see waterfall.py)
L_CENTRAL = 3.50
BOLT_TBTU = {2027: 0.0, 2028: 10 * 0.1 * 52, 2029: (10 * 0.75 + 6.4 * 0.5) * 52, 2030: 16.4 * 52, 2031: 16.4 * 52}
BOLT_CAPEX = {2027: 4.0, 2028: 4.0, 2029: 2.7, 2030: 0.0, 2031: 0.0}   # ASSUMPTION: 16.4 MTPA x $650/t = 10.7bn
DIV = 0.04 * 4 * 2.498                      # common dividend, $bn a year
PARENT_COUPON = 0.0838

def series(L, cost_mode="central", bolt=True, cp2x=CP2X, flat_cost=None):
    vol = dict(V.vol); op = dict(V.open_tbtu); capex = dict(V.CAPEX)
    if not bolt:
        for y in YEARS:
            vol[y] -= BOLT_TBTU[y]; op[y] = max(0.0, op[y] - BOLT_TBTU[y]); capex[y] -= BOLT_CAPEX[y]
    fee = dict(FUT)
    def cost(y):
        if flat_cost is not None:
            return flat_cost * vol[y] / 1000
        if cost_mode == "calibrated":
            return C26 * vol[y] / 1000
        return (C_EX * vol[y]) / 1000 + BASIS[y]
    rows = {}
    for y in YEARS:
        con = vol[y] - op[y]
        rev_c = con * V.CONTRACT_FEE[y] / 1000 + (max(0.0, con - 1560) * cp2x / 1000 if y >= 2030 else 0.0)
        rev_o = op[y] * fee[y] / 1000
        c = cost(y)
        rows[y] = dict(vol=vol[y], open=op[y], con=con, ebitda=rev_c + rev_o - c, ec=rev_c - c * con / vol[y], eo=rev_o - c * op[y] / vol[y], capex=capex[y])
    # terminal, 2032 on
    y = 2031; con = vol[y] - op[y]; share_c = con / vol[y]
    c_unit = (flat_cost if flat_cost is not None else (C26 if cost_mode == "calibrated" else C_EX))
    term = dict(con=con, open=op[y], share_c=share_c, ec=con * (2.45 - c_unit) / 1000 + max(0.0, con - 1560) * cp2x / 1000 - 1.0 * share_c,
                eo=op[y] * (L - c_unit) / 1000 - 1.0 * (1 - share_c), conv=con * (L - c_unit) / 1000)
    return rows, term

def net_debt_path(rows):
    nd = V.ND0; out = {}
    for i, y in enumerate(YEARS):
        e = rows[y]["ebitda"]; interest = nd * V.DEBT_COST
        cash_tax = V.TAX * max(0.0, e - interest - (1.0 + 0.3 * i))
        fcf = e - interest - cash_tax - rows[y]["capex"] - V.PREF - V.NCI - DIV
        nd -= fcf; out[y] = (nd, fcf, interest)
    return out

def value(L, cost_mode="central", bolt=True, cp2x=CP2X, roll=False, rc=S.RC, ro=S.RO, flat_cost=None, uplift=0.0):
    rows, term = series(L, cost_mode, bolt, cp2x, flat_cost)
    yrs = [2029, 2030, 2031] if roll else YEARS
    pv = 0.0
    for t, y in enumerate(yrs, start=1):
        r = rows[y]
        ec = r["ec"] + (uplift if y >= 2029 else 0.0)
        pv += (ec * (1 - V.TAX) + V.TAX * S.DA[y]) / (1 + rc) ** t + r["eo"] * (1 - V.TAX) / (1 + ro) ** t - r["capex"] / (1 + rc) ** t
    n_y = len(yrs); n = 2049 - 2031
    cc = (term["ec"] + uplift) * (1 - V.TAX) + V.TAX * 2.6
    pv += cc * (1 - (1 + rc) ** -n) / rc / (1 + rc) ** n_y
    pv += term["conv"] * (1 - V.TAX) / ro / (1 + ro) ** (n_y + n)
    pv += term["eo"] * (1 - V.TAX) / ro / (1 + ro) ** n_y
    nci = V.NCI * (1 - V.TAX) / rc
    nd = net_debt_path(rows)[2028][0] if roll else V.ND0
    return (pv - nd - S.PREF_LIQ - nci - S.BP) / V.SHARES

def needed(**kw):
    lo, hi = -5.0, 30.0
    for _ in range(80):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if value(m, **kw) < PX else (lo, m)
    return m

if __name__ == "__main__":
    print("LEGACY v7 model; v8 numbers are in results/model_v8.txt")
    L_ = []
    L_.append(f"price {PX} (Oct 7 close); CME futures fees 2027-31: " + ", ".join(f"{y} {FUT[y]:.2f}" for y in YEARS))
    L_.append(f"cost: 2026 calibrated {C26:.3f}/MMBtu; underlying ex-basis {C_EX:.3f}/MMBtu; Plaquemines basis {BASIS26:.3f}bn in 2026-27, half in 2028, zero from 2029")
    v0 = value(L_CENTRAL); v28 = value(L_CENTRAL, roll=True)
    ke = ((v28 + 2 * 0.16) / v0) ** (1 / 2.23) - 1 if v0 > 0 else float("nan")
    L_.append(f"CENTRAL (futures to 2031, then {L_CENTRAL:.2f}; central costs; bolt-ons in; CP2 +{CP2X}): today {v0:.2f}, end-2028 {v28:.2f}, implied equity return {ke:.1%} a year incl. dividends")
    L_.append(f"  fee the price needs from 2032 (futures kept to 2031): {needed():.2f}")
    for lab, kw in (("calibrated costs (v6 basis)", dict(cost_mode="calibrated")), ("ex bolt-ons", dict(bolt=False)), ("CP2 +0.00", dict(cp2x=0.0)), ("CP2 +0.85", dict(cp2x=0.85))):
        L_.append(f"  {lab:<28} today {value(L_CENTRAL, **kw):6.2f}  end-2028 {value(L_CENTRAL, roll=True, **kw):6.2f}  needs {needed(**kw):5.2f}")
    # long-run fee line
    L_.append("long-run fee from 2032 -> value today (central costs) | end-2028 | today, calibrated costs | today ex bolt-ons")
    pay = []
    for x in [i / 2 for i in range(0, 17)]:
        r = (x, value(x), value(x, roll=True), value(x, cost_mode="calibrated"), value(x, bolt=False))
        pay.append(r); L_.append("  {:4.1f}  {:7.2f}  {:7.2f}  {:7.2f}  {:7.2f}".format(*r))
    slope = (value(4.5) - value(2.5)) / 2
    L_.append(f"each $1 of long-run fee from 2032 is worth {slope:.2f} a share today ({slope / PX:.0%} of price)")
    hh = value(L_CENTRAL) - value(L_CENTRAL - 1.15)
    L_.append(f"Henry Hub +$1 for good (JKM unchanged) ~ -1.15 on the long-run fee: {-hh:.2f} a share (long-run only; 2027-31 futures held)")
    # grid
    costs = [1.15, 0.92, 0.75, 0.60]
    Ls = [2.5, 3.0, 3.5, 4.0, 4.5, 5.19, 6.0]
    L_.append("grid: value today by long-run fee (rows) and flat cost per MMBtu (columns " + ", ".join(f"{c:.2f}" for c in costs) + ")")
    grid = []
    for l in Ls:
        g = [value(l, flat_cost=c) for c in costs]; grid.append([l] + g)
        L_.append(f"  {l:4.2f}  " + "  ".join(f"{v:7.2f}" for v in g))
    # management framework reconciliation
    rows, _ = series(3.0)
    con29 = rows[2029]["con"]; op29 = rows[2029]["open"]
    mine3 = rows[2029]["ebitda"] - op29 * (FUT[2029] - 3.0) / 1000
    L_.append(f"2029 EBITDA at a $3 open fee, central costs, Aug volumes: {mine3:.2f}bn (management, March: about 11; $5 -> 17)")
    L_.append(f"  March framework implies {3000:.0f} TBtu of 2029 open volume ($3.0bn per $1); May deck 1,850 ($1.80-1.90bn); Aug deck 2,475 ($2.45-2.50bn)")
    extra = (3000 - op29) * (3.0 - C_EX) / 1000
    L_.append(f"  the extra ~{3000 - op29:.0f} TBtu of open volume in the March framework is worth ~{extra:.2f}bn at $3; remaining gap {11.0 - mine3 - extra:.2f}bn")
    gap = 11.0 - mine3
    L_.append(f"  if management's 11bn is right (gap {gap:.2f}bn added from 2029): today {value(L_CENTRAL, uplift=gap):.2f}, needs {needed(uplift=gap):.2f}")
    # three-statement summary on central
    nd = net_debt_path(series(L_CENTRAL)[0])
    L_.append("central path: year, EBITDA, EPS, FCF after dividends, net debt, ND/EBITDA")
    rows, _ = series(L_CENTRAL)
    from eps_path import DA as DA_
    for y in YEARS:
        e = rows[y]["ebitda"]; ndy, fcf, interest = nd[y]
        ebt = e - DA_[y] - interest; ni = ebt - V.TAX * max(0, ebt) - V.PREF - V.NCI
        L_.append(f"  {y}  {e:6.2f}  {ni / V.SHARES:5.2f}  {fcf:6.2f}  {ndy:5.1f}  {ndy / e:4.1f}x")
    for y in (2030, 2031):
        e = rows[y]["ebitda"]; ndy = nd[y][0]
        for m, lab in ((8.1, "VG"), (10.3, "Cheniere")):
            eq = (m * e - ndy - S.PREF_LIQ - V.NCI * (1 - V.TAX) / S.RC - S.BP) / V.SHARES
            L_.append(f"  multiple check {y} at {lab} {m}x: {eq:.2f}/share in {y}, {eq / 1.12 ** (y - 2026.8):.2f} today at 12%")
    out = "\n".join(L_); print(out)
    open(os.path.join(RESULTS, "model_v7_on_current_curve.txt"), "w").write(out + "\n")
    with open(os.path.join(RESULTS, "payoff_v7_on_current_curve.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["long_run_fee_from_2032", "today_central", "end2028_central", "today_calibrated_costs", "today_ex_boltons"])
        for r in pay: w.writerow([f"{x:.2f}" for x in r])
    with open(os.path.join(RESULTS, "grid_v7_on_current_curve.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["long_run_fee"] + [f"cost_{c:.2f}" for c in costs])
        for r in grid: w.writerow([f"{x:.2f}" for x in r])
