"""v9 valuation and earnings: the single source of truth for every number in the v9 piece.

Built on model_v8.py (escalation, 10-Q interest calibration, capitalized interest, 7 Oct curve), plus:
1. D&A rebuilt from the balance sheet. Depreciation ran at 1,012m a year in H1 2026 on 37.7bn of
   in-service gross plant (10-Q Note 5), 2.68% a year. Future D&A applies that rate to in-service
   plant, adding (ASSUMPTION, mid-year convention): two tankers (0.5bn, 2H 2026), the rest of
   Plaquemines and other non-CP2 construction (3.25bn, mid-2027), CP2 (cost basis 30bn less the
   commissioning margin credited to construction in progress; Phase 1, 55%, mid-2028; Phase 2
   mid-2030), CP2 bolt-on (6.5bn, mid-2029) and Plaquemines bolt-on (4.2bn, mid-2030).
2. Reported vs cash EBITDA. The 10-Q: commissioning-cargo proceeds reduce construction in progress
   "until assets are placed in service from an accounting perspective"; Consolidated Adjusted EBITDA
   is built up from GAAP net income, so those margins never reach reported EBITDA or EPS. Cash and
   value are unaffected. ASSUMPTION for the TBtu credited to CIP (CP2 and bolt-on output before each
   phase is placed in service): 2027 192 (all of CP2's first output: 2,220 TBtu outlook less
   Calcasieu ~572 and Plaquemines ~1,456), 2028 425, 2029 380, 2030 150, 2031 0.
3. Discount rates checked against the market: VGLNG priced 6.375% 2034 and 6.625% 2036 secured notes
   at par in June 2026, so 7% for contracted cash sits ~40-60bp above the marginal secured cost.
   Sensitivities at 8% contracted and 12% open.
4. Symmetric inflation: fee from 2032 and costs both rising 2.5% a year (real-flat), next to the
   one-sided case (costs rise, fee flat).
5. Long-run marginal cost (LRMC) of a new US export project from recent FID costs (data/lrmc_capex_comps.csv).
6. Scenarios with weights (judgement, stated): bear $2.50 (30%), base $3.50 (50%), bull $4.50 (20%).
7. 2027 EPS bridge to consensus, pair exposure vs Cheniere, put-spread payoffs.
"""
import os, io, csv, contextlib, math
with contextlib.redirect_stdout(io.StringIO()):
    import valuation as V
    import sotp as S
    import model_v8 as M8
from common import RESULTS, read

PX = M8.PX; YEARS = M8.YEARS; FUT = M8.FUT; C_EX = M8.C_EX; BASIS = M8.BASIS
L_CENTRAL = 3.50; CP2X = M8.CP2X; TAX = V.TAX; SH = V.SHARES
dep = {r["item"]: r["value"] for r in read("depreciation_inputs_2026-06-30.csv")}
INSERVICE0 = (float(dep["terminal_and_pipeline_facilities_gross"]) + float(dep["lng_tankers_gross"]) + float(dep["other_ppe_gross"])) / 1000
DA_RATE = float(dep["depreciation_expense_h1_2026"]) * 2 / 1000 / INSERVICE0
AMORT = (float(dep["depreciation_and_amortization_h1_2026"]) - float(dep["depreciation_expense_h1_2026"])) * 2 / 1000
CP2_COST = 30.0                          # ASSUMPTION: $15bn spent by Aug 2026 (deck) + my remaining CP2 capex
CIP_TBTU = {2027: 192.0, 2028: 425.0, 2029: 380.0, 2030: 150.0, 2031: 0.0}

def cip_margin(y, L=L_CENTRAL, cost_infl=0.0):
    return CIP_TBTU[y] * (FUT[y] - M8.unit_cost(y, C_EX, cost_infl)) / 1000

def da_schedule(cip=True):
    """Book D&A by year, mid-year convention. Returns {year: D&A} for 2026-2031 and 2031 run-rate."""
    credited = sum(cip_margin(y) for y in (2027, 2028, 2029, 2030)) if cip else 0.0
    cp2_net = CP2_COST - credited
    adds = {2026.5: 0.5, 2027.5: 3.25, 2028.5: 0.55 * cp2_net, 2029.5: 6.5, 2030.5: 0.45 * cp2_net + 4.2}
    out = {}
    for y in [2026] + YEARS:
        g = INSERVICE0 + sum(a * (1.0 if t < y else (0.5 if int(t) == y else 0.0)) for t, a in adds.items())
        out[y] = DA_RATE * g + AMORT
    full = INSERVICE0 + sum(adds.values())
    return out, DA_RATE * full + AMORT

DA9, DA_RUN = da_schedule(True)

def series(L, cost_mode="central", bolt=True, cp2x=CP2X, flat_cost=None, escal=True, cost_infl=0.0, fee_infl=0.0):
    rows, term = M8.series(L, cost_mode, bolt, cp2x, flat_cost, escal, cost_infl)
    if fee_infl:
        y0 = 2031; op = term["open"]; share_c = term["share_c"]
        c_unit0 = flat_cost if flat_cost is not None else (M8.C26 if cost_mode == "calibrated" else C_EX)
        tail = []
        for y, ec, eo in term["tail"]:
            Ly = L * (1 + fee_infl) ** (y - 2032)
            cu = M8.unit_cost(y, c_unit0, cost_infl)
            tail.append((y, ec, op * (Ly - cu) / 1000 - 1.0 * (1 - share_c)))
        term = dict(term, tail=tail, L49=L * (1 + fee_infl) ** (M8.RUNOFF - 2032))
    return rows, term

def value(L, roll=False, rc=S.RC, ro=S.RO, uplift=0.0, fee_infl=0.0, cost_infl=0.0, da=None, **kw):
    da = DA9 if da is None else da
    rows, term = series(L, cost_infl=cost_infl, fee_infl=fee_infl, **kw)
    base_year = 2028 if roll else 2026
    yrs = [2029, 2030, 2031] if roll else YEARS
    pv = 0.0
    for y in yrs:
        t = y - base_year; r = rows[y]
        ec = r["ec"] + (uplift if y >= 2029 else 0.0)
        pv += (ec * (1 - TAX) + TAX * da[y]) / (1 + rc) ** t + r["eo"] * (1 - TAX) / (1 + ro) ** t - r["capex"] / (1 + rc) ** t
    for y, ec, eo in term["tail"]:
        t = y - base_year
        pv += ((ec + uplift) * (1 - TAX) + TAX * DA_RUN) / (1 + rc) ** t + eo * (1 - TAX) / (1 + ro) ** t
    tN = M8.RUNOFF - base_year
    vol31 = term["con"] + term["open"]
    if fee_infl:
        g = fee_infl
        L49 = term["L49"]; cu49 = M8.unit_cost(M8.RUNOFF, C_EX if kw.get("flat_cost") is None else kw["flat_cost"], cost_infl)
        cf50 = (vol31 * (L49 * (1 + g) - cu49 * (1 + cost_infl)) / 1000 - 1.0) * (1 - TAX)
        pv += cf50 / (ro - g) / (1 + ro) ** tN
    else:
        pv += term["eo_perp"] * (1 - TAX) / ro / (1 + ro) ** tN
        pv += term["conv"] * (1 - TAX) / ro / (1 + ro) ** tN
    nci = V.NCI * (1 - TAX) / rc
    nd = net_debt_path(rows)[2028]["nd"] if roll else M8.ND0
    return (pv - nd - S.PREF_LIQ - nci - S.BP) / SH

def net_debt_path(rows, cip=True):
    nd = M8.ND0; out = {}
    for i, y in enumerate(YEARS):
        e_cash = rows[y]["ebitda"]
        e_rep = e_cash - (cip_margin(y) if cip else 0.0)
        cash_int = nd * M8.CASH_RATE
        cash_tax = TAX * max(0.0, e_rep - (cash_int - M8.CAPI[y]) - (1.0 + 0.3 * i))
        fcf = e_cash - cash_int - cash_tax - rows[y]["capex"] - V.PREF - V.NCI - M8.DIV
        pl_int = nd * M8.PL_RATE - M8.CAPI[y]
        nd -= fcf
        out[y] = dict(nd=nd, fcf=fcf, cash_int=cash_int, pl_int=pl_int, cash_tax=cash_tax, e_rep=e_rep, e_cash=e_cash)
    return out

def eps_path(L=L_CENTRAL, cip=True, da=None, **kw):
    da = DA9 if da is None else da
    rows, _ = series(L, **kw); nd = net_debt_path(rows, cip)
    out = {}
    for y in YEARS:
        d = nd[y]; ebt = d["e_rep"] - da[y] - d["pl_int"]
        out[y] = dict(eps=(ebt - TAX * max(0, ebt) - V.PREF - V.NCI) / SH, e_rep=d["e_rep"], e_cash=d["e_cash"], da=da[y],
                      pl_int=d["pl_int"], fcf=d["fcf"], nd=d["nd"])
    return out

def needed(**kw):
    lo, hi = -5.0, 30.0
    for _ in range(80):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if value(m, **kw) < PX else (lo, m)
    return m

def lrmc(usd_t, hurdle=0.08, opex=C_EX, years=20, build=(0.15, 0.30, 0.35, 0.20), tax=0.21, bonus=True):
    """Flat fee per MMBtu of nameplate that gives the after-tax unlevered hurdle on a new US project."""
    cap = usd_t / 52.0                           # $ per MMBtu-a-year of nameplate
    pv_cap = sum(w * cap / (1 + hurdle) ** (i - len(build)) for i, w in enumerate(build))   # value at COD
    ann = (1 - (1 + hurdle) ** -years) / hurdle
    if bonus:
        shield = tax * cap                       # expensed at COD (OBBBA 100% bonus)
    else:                                        # 15-year MACRS, 150% DB
        rates = [0.05, 0.095, 0.0855, 0.077, 0.0693, 0.0623, 0.059, 0.059, 0.0591, 0.059, 0.0591, 0.059, 0.0591, 0.059, 0.0591, 0.0295]
        shield = sum(tax * cap * r / (1 + hurdle) ** (k + 1) for k, r in enumerate(rates))
    # (fee - opex) * (1 - tax) * ann + shield = pv_cap
    return opex + (pv_cap - shield) / ((1 - tax) * ann)

def bonus_upside():
    """PV per share if 2027-29 CP2 and bolt-on capex were fully expensed for tax instead of book-depreciated."""
    pv = 0.0
    for t, y in enumerate(YEARS, start=1):
        c = V.CAPEX[y]
        pv += TAX * c / (1 + S.RC) ** t
        pv -= sum(TAX * c * DA_RATE / (1 + S.RC) ** (t + k) for k in range(1, 38))
    return pv / SH

if __name__ == "__main__":
    L_ = []
    v0 = value(L_CENTRAL); v28 = value(L_CENTRAL, roll=True)
    ke = ((v28 + 2 * 0.16) / v0) ** (1 / 2.23) - 1
    L_.append(f"price {PX}; CME (7 Oct) fees 2027-31: " + ", ".join(f"{FUT[y]:.2f}" for y in YEARS))
    L_.append(f"D&A rate {DA_RATE:.4f} on in-service gross {INSERVICE0:.2f}bn (+ amortization {AMORT:.3f}); D&A: " + ", ".join(f"{y} {DA9[y]:.2f}" for y in DA9) + f"; run-rate {DA_RUN:.2f}")
    L_.append(f"CENTRAL: today {v0:.2f}, end-2028 {v28:.2f}, implied equity return {ke:.1%}; needs {needed():.2f}; slope {(value(4.5) - value(2.5)) / 2:.2f}")
    v8_0 = M8.value(L_CENTRAL)
    L_.append(f"  vs v8 (old D&A shield): {v8_0:.2f}")
    # discount-rate sensitivities
    for rc, ro in ((0.07, 0.10), (0.08, 0.10), (0.07, 0.12), (0.08, 0.12), (0.06, 0.09)):
        L_.append(f"  rates contracted {rc:.0%} / open {ro:.0%}: today {value(L_CENTRAL, rc=rc, ro=ro):6.2f}  end-2028 {value(L_CENTRAL, roll=True, rc=rc, ro=ro):6.2f}  needs {needed(rc=rc, ro=ro):5.2f}")
    # inflation
    for lab, kw in (("costs +2.5%/yr, fee flat", dict(cost_infl=0.025)), ("fee and costs +2.5%/yr (real-flat)", dict(cost_infl=0.025, fee_infl=0.025)),
                    ("fee +2.5%/yr, costs flat", dict(fee_infl=0.025)), ("no escalation", dict(escal=False)), ("ex bolt-ons", dict(bolt=False)),
                    ("CP2 +0.00", dict(cp2x=0.0)), ("CP2 +0.85", dict(cp2x=0.85)), ("calibrated costs", dict(cost_mode="calibrated"))):
        L_.append(f"  {lab:<36} today {value(L_CENTRAL, **kw):6.2f}  end-2028 {value(L_CENTRAL, roll=True, **kw):6.2f}  needs {needed(**kw):5.2f}")
    L_.append(f"  bonus-depreciation upside if 2027-31 capex were expensed for tax: +{bonus_upside():.2f} a share (not in central)")
    # scenarios
    W = (("bear: long-run fee 2.50", 2.50, 0.30), ("base: 3.50", 3.50, 0.50), ("bull: 4.50", 4.50, 0.20))
    ev0 = ev28 = 0.0; sc = []
    for lab, l, w in W:
        a, b = value(l), value(l, roll=True); ev0 += w * a; ev28 += w * b
        tr = (b + 0.32) / PX - 1
        sc.append((lab, l, w, a, b, tr)); L_.append(f"  scenario {lab:<26} weight {w:.0%}: today {a:6.2f}  end-2028 {b:6.2f}  VG 24-month total return {tr:+.0%}")
    L_.append(f"  probability-weighted: today {ev0:.2f}, end-2028 {ev28:.2f} (weighted fee {sum(l * w for _, l, w in W):.2f})")
    # management framework
    rows, _ = series(3.0); op29 = rows[2029]["open"]
    mine3 = rows[2029]["ebitda"] - op29 * (FUT[2029] - 3.0) / 1000; gap = 11.0 - mine3
    L_.append(f"management 2029 at $3: mine {mine3:.2f} (cash basis); gap {gap:.2f}; if right: today {value(L_CENTRAL, uplift=gap):.2f}, needs {needed(uplift=gap):.2f}")
    # LRMC
    comps = read("lrmc_capex_comps.csv")
    L_.append("LRMC: flat 20-year fee a new US project needs (opex = VG's 0.92; 4-year build; 21% tax):")
    lr = []
    for r in comps:
        t = float(r["usd_per_tonne"])
        a, b, c, d = lrmc(t, 0.08), lrmc(t, 0.07), lrmc(t, 0.08, bonus=False), lrmc(t, 0.08, opex=0.60)
        lr.append((r["project"], r["type"], t, a, b, c, d))
        L_.append(f"  {r['project']:<38} {t:6.0f}/t: 8% {a:.2f} | 7% {b:.2f} | 8% no bonus {c:.2f} | 8% opex 0.60 {d:.2f}")
    # EPS bridge 2027
    e_cash_old = M8.series(L_CENTRAL)[0]
    v8eps = {}
    nd8 = M8.net_debt_path(e_cash_old)
    from eps_path import DA as DA_OLD
    for y in YEARS:
        e = e_cash_old[y]["ebitda"]; ebt = e - DA_OLD[y] - nd8[y]["pl_int"]
        v8eps[y] = (ebt - TAX * max(0, ebt) - V.PREF - V.NCI) / SH
    p_noncip = eps_path(cip=False); p = eps_path()
    L_.append("EPS path v9 (reported basis): year, cash EBITDA, CIP-credited margin, reported EBITDA, D&A, P&L interest, EPS, FCF, net debt")
    for y in YEARS:
        L_.append(f"  {y}  {p[y]['e_cash']:6.2f}  {p[y]['e_cash'] - p[y]['e_rep']:5.2f}  {p[y]['e_rep']:6.2f}  {p[y]['da']:4.2f}  {p[y]['pl_int']:4.2f}  {p[y]['eps']:5.2f}  {p[y]['fcf']:6.2f}  {p[y]['nd']:5.1f}")
    y = 2027
    step_da = p_noncip[y]["eps"] - v8eps[y]
    step_cip = p[y]["eps"] - p_noncip[y]["eps"]
    op27 = V.open_tbtu[2027] - CIP_TBTU[2027]
    need_drop = (p[y]["eps"] - 1.00) * SH / (1 - TAX)        # pre-tax EBITDA the Street must be missing
    fee_street = FUT[2027] - need_drop * 1000 / op27
    L_.append(f"2027 EPS bridge: v8 {v8eps[y]:.2f} -> D&A rebuilt {step_da:+.2f} -> CP2 commissioning to CIP {step_cip:+.2f} -> v9 reported {p[y]['eps']:.2f}; consensus 1.00 needs {need_drop:.2f}bn less pre-tax EBITDA, i.e. the remaining {op27:.0f} TBtu open at ~{fee_street:.2f} vs strip {FUT[2027]:.2f}")
    # pair exposure
    ch = {r["item"]: r["value"] for r in read("cheniere_exposure_2026-10-08.csv")}
    ch_open = (1 - float(ch["share_contracted_through_mid_2030s"])) * float(ch["production_guidance_2026_mid"]) * 52
    ch_per = ch_open / 1000 * (1 - 0.21) / 0.10 / (float(ch["shares_outstanding"]) / 1000)
    slope = (value(4.5) - value(2.5)) / 2
    L_.append(f"pair: $1 of long-run fee = {slope:.2f}/sh VG ({slope / PX:.0%} of price) vs ~{ch_per:.2f}/sh Cheniere ({ch_per / float(ch['close_2026-10-07']):.1%}); Cheniere open ~{ch_open:.0f} TBtu (5% of {ch['production_guidance_2026_mid']} Mt)")
    # put spread
    opt = {(r["expiry"], float(r["strike"])): float(r["last_price"]) for r in read("vg_options_last_2026-10-07.csv")}
    cost = opt[("2029-01-19", 12.5)] - opt[("2029-01-19", 10.0)]
    L_.append(f"Jan-2029 12.5/10 put spread, last trades: cost {cost:.2f}, max {2.5:.2f}")
    for lab, l, w, a, b, tr in sc:
        pay = min(2.5, max(0.0, 12.5 - b))
        L_.append(f"  at the {lab} end-2028 value {b:.2f}: payoff {pay:.2f}, return {pay / cost - 1:+.0%}")
    # cross-check against VG's own $138bn total contracted third-party revenue (Q2 2026 deck, slide 22)
    esc = lambda y, first: 1 + 0.175 * (1.025 ** max(0, y - first + 1) - 1)
    trs = [(8.5, 2025.3, 2045.3, 2027), (1.0, 2025.3, 2028.3, 2027), (0.5, 2025.3, 2030.3, 2027), (13.0, 2026.9, 2046.9, 2028),
           (0.3, 2026.9, 2030.9, 2028), (6.7, 2027.5, 2047.5, 2029), (9.5, 2029.5, 2049.5, 2031), (9.5, 2030.5, 2050.5, 2032), (3.0, 2026.0, 2031.0, 2027)]
    vol = volesc = 0.0
    for m_, s_, e_, f_ in trs:
        for y in range(2026, 2052):
            a, b = max(s_, 2026.6, y), min(e_, y + 1)
            if b > a:
                v = m_ * 0.052 * (b - a); vol += v; volesc += v * esc(y, f_)
    imp = {lift: (138 - lift * vol) / volesc for lift in (0.0, 0.30, 0.60)}
    L_.append(f"$138bn cross-check: {vol:.1f}bn MMBtu remaining; implied average base fixed fee {imp[0.0]:.2f} (net lifting 0), {imp[0.30]:.2f} (0.30), {imp[0.60]:.2f} (0.60 = 15% of $4)")
    orig = M8.contracted_rev
    for shift, lab in ((0.35, "contract fees -0.35 from 2029 (to ~2.10) and CP2 premium 0")
                       ,):
        M8.contracted_rev = lambda y, con, fee, cp2x, on, _o=orig, _s=shift: _o(y, con, fee - (_s if y >= 2029 else 0.0), cp2x, on)
        a, b, c = value(L_CENTRAL, cp2x=0.0), value(L_CENTRAL, roll=True, cp2x=0.0), needed(cp2x=0.0)
        M8.contracted_rev = orig
        L_.append(f"  {lab}: today {a:.2f}, end-2028 {b:.2f}, needs {c:.2f}")
    # 2026 EPS on reported interest and rebuilt D&A
    e26 = (V.bs["ebitda_guide_2026_low"] + V.bs["ebitda_guide_2026_high"]) / 2000; int26 = (933 + 2 * 489) / 1000
    eps26 = ((e26 - DA9[2026] - int26) * (1 - TAX) - V.PREF - V.NCI) / SH
    L_.append(f"2026 EPS (guidance midpoint, reported interest, D&A {DA9[2026]:.2f}): {eps26:.2f}")
    # grid, cost and fee thresholds, Henry Hub
    costs = [1.15, 0.92, 0.75, 0.60]; Ls = [2.5, 3.0, 3.5, 4.0, 4.5, 5.19, 6.0]; grid = []
    L_.append("grid: today by long-run fee (rows) x flat cost (cols 1.15, 0.92, 0.75, 0.60)")
    for l in Ls:
        g = [value(l, flat_cost=c) for c in costs]; grid.append([l] + g)
        L_.append(f"  {l:4.2f}  " + "  ".join(f"{v:6.2f}" for v in g))
    lo, hi = 0.0, 1.5
    for _ in range(60):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if value(3.5, flat_cost=m) > PX else (lo, m)
    L_.append(f"  at 3.50 the price needs a flat cost of {m:.3f}; at 0.92 flat it needs a fee of {needed(flat_cost=0.92):.2f}; 0.92 vs 1.15 flat at 3.50 = {value(3.5, flat_cost=0.92) - value(3.5, flat_cost=1.15):.2f}/sh; central vs calibrated = {v0 - value(L_CENTRAL, cost_mode='calibrated'):.2f}/sh")
    L_.append(f"Henry Hub +$1 for good: {value(L_CENTRAL - 1.15) - v0:.2f}/sh")
    nd = net_debt_path(series(L_CENTRAL)[0])
    for y in (2030, 2031):
        e = nd[y]["e_rep"]; ndy = nd[y]["nd"]
        for mlt, lab in ((8.1, "VG"), (10.3, "Cheniere")):
            eq = (mlt * e - ndy - S.PREF_LIQ - V.NCI * (1 - TAX) / S.RC - S.BP) / SH
            L_.append(f"  multiple check {y} reported EBITDA {e:.2f} at {lab} {mlt}x: {eq:.2f} in {y}, {eq / 1.12 ** (y - 2026.8):.2f} today at 12%")
    with open(os.path.join(RESULTS, "grid_v9.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["long_run_fee"] + [f"cost_{c:.2f}" for c in costs])
        for r in grid: w.writerow([f"{x:.2f}" for x in r])
    out = "\n".join(L_); print(out)
    open(os.path.join(RESULTS, "model_v9.txt"), "w").write(out + "\n")
    with open(os.path.join(RESULTS, "eps_path_v9.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["year", "cash_ebitda", "cip_credited_margin", "reported_ebitda", "da", "pl_interest", "eps_reported", "eps_v8", "fcf_after_div", "net_debt"])
        for y in YEARS:
            w.writerow([y] + [f"{x:.2f}" for x in (p[y]["e_cash"], p[y]["e_cash"] - p[y]["e_rep"], p[y]["e_rep"], p[y]["da"], p[y]["pl_int"], p[y]["eps"], v8eps[y], p[y]["fcf"], p[y]["nd"])])
    with open(os.path.join(RESULTS, "lrmc_v9.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["project", "type", "usd_per_tonne", "fee_8pct", "fee_7pct", "fee_8pct_no_bonus", "fee_8pct_opex_060"])
        for r in lr: w.writerow([r[0], r[1], f"{r[2]:.0f}"] + [f"{x:.2f}" for x in r[3:]])
    with open(os.path.join(RESULTS, "scenarios_v9.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["scenario", "long_run_fee", "weight", "value_today", "value_end2028", "vg_24m_total_return"])
        for r in sc: w.writerow([r[0], r[1], r[2], f"{r[3]:.2f}", f"{r[4]:.2f}", f"{r[5]:.3f}"])
    with open(os.path.join(RESULTS, "payoff_v9.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["long_run_fee_from_2032", "today", "end2028", "today_real_flat", "today_costs_inflating"])
        for i in range(17):
            x = i / 2
            w.writerow([f"{x:.2f}"] + [f"{v:.2f}" for v in (value(x), value(x, roll=True), value(x, cost_infl=0.025, fee_infl=0.025), value(x, cost_infl=0.025))])
