"""v10 valuation and earnings: the single source of truth for every number in the v10 piece.

Changes from model_v9.py (kept as the v9 record):
1. Accounting, central case = revenue. The FY2024 10-K: "In December 2024, we first produced LNG
   [at Plaquemines] ... In December 2024, a portion of the facility's assets, representing $11.4
   billion of costs, were placed in service in accordance with GAAP." Placement came the month of
   first LNG, so only test-LNG proceeds go to construction in progress. Central: CP2 Phase 1 (55% of
   a 30bn cost basis, ASSUMPTION) placed in service at first LNG (Q4 2027, 2027.75), Phase 2 mid-2028,
   CP2 bolt-on late 2028, Plaquemines bolt-on mid-2029. The v9 reading (commissioning output credited
   to construction cost) is kept as a sensitivity.
2. Capitalized interest follows those dates (ASSUMPTION): 1.4bn 2027, 0.7bn 2028, 0.3bn 2029, none after.
3. Scenarios: four, with the management case weighted explicitly: bear $2.50 (25%), base $3.50 (45%),
   bull $4.50 (20%), management's 2029 framework (10%). Weights are judgement.
4. LRMC over the full asset life (35 years: 20 contracted, 15 more at the same fee) next to the
   20-year version.
5. CP2 delay of 6 and 12 months (volume shifted later; capex unchanged; no overrun modelled).
6. Judgment audit: every call, which way it pushes value, and by how much.
7. Cost of equity from CAPM (beta since IPO, 10-year Treasury, Damodaran's implied ERP).
8. Fee history by market regime (TTF basis 2010-2026, JKM basis 2017-2026).
"""
import os, io, csv, contextlib, math
from statistics import mean, median
with contextlib.redirect_stdout(io.StringIO()):
    import valuation as V
    import sotp as S
    import model_v8 as M8
    import model_v9 as M9
from common import RESULTS, read

PX = M8.PX; YEARS = M8.YEARS; FUT = M8.FUT; C_EX = M8.C_EX; BASIS = M8.BASIS
L_CENTRAL = 3.50; TAX = V.TAX; SH = V.SHARES
CAPI10 = {2027: 1.4, 2028: 0.7, 2029: 0.3, 2030: 0.0, 2031: 0.0}
CIP_V9 = dict(M9.CIP_TBTU)
CIP_ZERO = {y: 0.0 for y in YEARS}
CP2_COST = M9.CP2_COST
mk = {r["item"]: float(r["value"]) for r in read("market_inputs_2026-10-08.csv")}

def cip_margin(y, cip):
    return cip[y] * (FUT[y] - C_EX) / 1000

def da_schedule(cip=CIP_ZERO, timing="central"):
    credited = sum(cip_margin(y, cip) for y in YEARS)
    net = CP2_COST - credited
    if timing == "central":
        adds = {2026.5: 0.5, 2027.5: 3.25, 2027.75: 0.55 * net, 2028.5: 0.45 * net, 2028.9: 6.5, 2029.5: 4.2}
    else:   # v9 timing
        adds = {2026.5: 0.5, 2027.5: 3.25, 2028.5: 0.55 * net, 2029.5: 6.5, 2030.5: 0.45 * net + 4.2}
    out = {}
    for y in [2026] + YEARS:
        g = M9.INSERVICE0 + sum(a * (1.0 if t < y else ((y + 1 - t) if int(t) == y else 0.0)) for t, a in adds.items())
        out[y] = M9.DA_RATE * g + M9.AMORT
    return out, M9.DA_RATE * (M9.INSERVICE0 + sum(adds.values())) + M9.AMORT

DA10, DA_RUN10 = da_schedule()

def series(L, delay=0.0, **kw):
    """M8 series with an optional CP2 delay (years): CP2 volume shifted later, open volume reduced first."""
    if not delay:
        return M9.series(L, **kw)
    vol0, op0 = dict(V.vol), dict(V.open_tbtu)
    cp2 = {y: V.vol[y] - 572 - 1456 - M8.BOLT_TBTU[y] for y in YEARS}
    cp2[2026] = 0.0
    def shifted(y):
        x = y - delay; lo = math.floor(x); f = x - lo
        a = cp2.get(lo, 0.0 if lo < 2027 else cp2[2031]); b = cp2.get(lo + 1, cp2[2031])
        return a * (1 - f) + b * f
    try:
        for y in YEARS:
            d = max(0.0, cp2[y] - shifted(y))
            V.vol[y] = vol0[y] - d
            V.open_tbtu[y] = max(0.0, op0[y] - d)
        return M9.series(L, **kw)
    finally:
        V.vol.clear(); V.vol.update(vol0); V.open_tbtu.clear(); V.open_tbtu.update(op0)

def net_debt_path(rows, cip=CIP_ZERO, capi=CAPI10):
    nd = M8.ND0; out = {}
    for i, y in enumerate(YEARS):
        e_cash = rows[y]["ebitda"]; e_rep = e_cash - cip_margin(y, cip)
        cash_int = nd * M8.CASH_RATE
        cash_tax = TAX * max(0.0, e_rep - (cash_int - capi[y]) - (1.0 + 0.3 * i))
        fcf = e_cash - cash_int - cash_tax - rows[y]["capex"] - V.PREF - V.NCI - M8.DIV
        pl_int = nd * M8.PL_RATE - capi[y]
        nd -= fcf
        out[y] = dict(nd=nd, fcf=fcf, pl_int=pl_int, e_rep=e_rep, e_cash=e_cash)
    return out

def value(L, roll=False, rc=S.RC, ro=S.RO, uplift=0.0, fee_infl=0.0, cost_infl=0.0, delay=0.0, da=None, da_run=None, **kw):
    da = DA10 if da is None else da; da_run = DA_RUN10 if da_run is None else da_run
    with contextlib.redirect_stdout(io.StringIO()):
        rows, term = series(L, delay=delay, cost_infl=cost_infl, fee_infl=fee_infl, **kw)
    base_year = 2028 if roll else 2026
    yrs = [2029, 2030, 2031] if roll else YEARS
    pv = 0.0
    for y in yrs:
        t = y - base_year; r = rows[y]
        ec = r["ec"] + (uplift if y >= 2029 else 0.0)
        pv += (ec * (1 - TAX) + TAX * da[y]) / (1 + rc) ** t + r["eo"] * (1 - TAX) / (1 + ro) ** t - r["capex"] / (1 + rc) ** t
    for y, ec, eo in term["tail"]:
        t = y - base_year
        pv += ((ec + uplift) * (1 - TAX) + TAX * da_run) / (1 + rc) ** t + eo * (1 - TAX) / (1 + ro) ** t
    tN = M8.RUNOFF - base_year
    if fee_infl:
        g = fee_infl; vol31 = term["con"] + term["open"]
        cu49 = M8.unit_cost(M8.RUNOFF, C_EX if kw.get("flat_cost") is None else kw["flat_cost"], cost_infl)
        cf50 = (vol31 * (term["L49"] * (1 + g) - cu49 * (1 + cost_infl)) / 1000 - 1.0) * (1 - TAX)
        pv += cf50 / (ro - g) / (1 + ro) ** tN
    else:
        pv += term["eo_perp"] * (1 - TAX) / ro / (1 + ro) ** tN + term["conv"] * (1 - TAX) / ro / (1 + ro) ** tN
    nci = V.NCI * (1 - TAX) / rc
    nd = net_debt_path(rows)[2028]["nd"] if roll else M8.ND0
    return (pv - nd - S.PREF_LIQ - nci - S.BP) / SH

def needed(**kw):
    lo, hi = -5.0, 30.0
    for _ in range(80):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if value(m, **kw) < PX else (lo, m)
    return m

def eps_path(L=L_CENTRAL, cip=CIP_ZERO, da=None, capi=CAPI10, **kw):
    da = DA10 if da is None else da
    with contextlib.redirect_stdout(io.StringIO()):
        rows, _ = series(L, **kw)
    nd = net_debt_path(rows, cip, capi); out = {}
    for y in YEARS:
        d = nd[y]; ebt = d["e_rep"] - da[y] - d["pl_int"]
        out[y] = dict(eps=(ebt - TAX * max(0, ebt) - V.PREF - V.NCI) / SH, e_rep=d["e_rep"], e_cash=d["e_cash"], da=da[y], pl_int=d["pl_int"], fcf=d["fcf"], nd=d["nd"])
    return out

def lrmc(usd_t, hurdle=0.08, opex=C_EX, years=20, tail=0, build=(0.15, 0.30, 0.35, 0.20), tax=0.21, bonus=True):
    cap = usd_t / 52.0
    pv_cap = sum(w * cap / (1 + hurdle) ** (i - len(build)) for i, w in enumerate(build))
    n = years + tail
    ann = (1 - (1 + hurdle) ** -n) / hurdle
    shield = tax * cap if bonus else sum(tax * cap * r / (1 + hurdle) ** (k + 1) for k, r in enumerate(
        [0.05, 0.095, 0.0855, 0.077, 0.0693, 0.0623, 0.059, 0.059, 0.0591, 0.059, 0.0591, 0.059, 0.0591, 0.059, 0.0591, 0.0295]))
    return opex + (pv_cap - shield) / ((1 - tax) * ann)

def regimes():
    tt = {r["month"]: (float(r["ttf_imf_usd_mmbtu"]), float(r["henry_hub_usd_mmbtu"])) for r in read("fred_ttf_hh_monthly.csv")}
    jk = {r["month"]: float(r["jkm_usd_mmbtu"]) for r in read("jkm_imf_monthly.csv")}
    ttf = {m: t - 1.15 * h - 2 for m, (t, h) in tt.items()}
    jkm = {m: jk[m] - 1.15 * tt[m][1] - 2 for m in jk if m in tt}
    R = [("2011-14: post-Fukushima shortage", 2011, 2014), ("2015-20: Australia and first US wave", 2015, 2020),
         ("2021-22: post-COVID and Russia shortage", 2021, 2022), ("2023-25: rebalancing", 2023, 2025), ("2026 (to Sep): Hormuz war", 2026, 2026)]
    out = []
    for lab, a, b in R:
        x = [v for m, v in ttf.items() if a <= int(m[:4]) <= b]; z = [v for m, v in jkm.items() if a <= int(m[:4]) <= b]
        out.append((lab, mean(x), median(x), mean(z) if z else None, len(x)))
    return out

if __name__ == "__main__":
    L_ = []
    v0 = value(L_CENTRAL); v28 = value(L_CENTRAL, roll=True); ke = ((v28 + 2 * 0.16) / v0) ** (1 / 2.23) - 1
    slope = (value(4.5) - value(2.5)) / 2; slope28 = (value(4.5, roll=True) - value(2.5, roll=True)) / 2
    L_.append(f"price {PX}; fees 2027-31 " + ", ".join(f"{FUT[y]:.2f}" for y in YEARS))
    L_.append("D&A v10 (CP2 placed in service at first LNG): " + ", ".join(f"{y} {DA10[y]:.2f}" for y in DA10) + f"; run-rate {DA_RUN10:.2f}")
    L_.append(f"BASE: today {v0:.2f}, end-2028 {v28:.2f}, implied equity return {ke:.1%}, needs {needed():.2f}, slope {slope:.2f} (end-2028 {slope28:.2f})")
    # CAPM
    beta_ipo, rf, erp = 0.92, mk["us10y_2026-10-07"] / 100, mk["damodaran_implied_erp_2026-10-01"] / 100
    L_.append(f"CAPM: beta since IPO 0.92 (daily; v15 recompute 0.91, R^2 ~3%; weekly 0.40) vs SPY; since the war -2.6 daily; rf {rf:.2%}; ERP {erp:.2%} -> cost of equity {rf + beta_ipo * erp:.1%}")
    # regimes
    L_.append("fee by regime (TTF basis mean/median | JKM basis mean, 2017+):")
    reg = regimes()
    for lab, a, b, c, n in reg:
        L_.append(f"  {lab:<42} {a:6.2f} {b:6.2f} | {'' if c is None else f'{c:6.2f}'}  n={n}")
    L_.append(f"  IGU trade 2015 {mk['igu_lng_trade_2015']:.0f} Mt -> 2019 {mk['igu_lng_trade_2019']:.1f} Mt: +{mk['igu_lng_trade_2019'] / mk['igu_lng_trade_2015'] - 1:.0%}; IEA wave to 2030: +184 Mt on 437 Mt = +42%")
    # sensitivities
    sens = [("contracted 8% / open 10%", dict(rc=0.08)), ("contracted 7% / open 12%", dict(ro=0.12)), ("CAPM-consistent 6% / 9%", dict(rc=0.06, ro=0.09)),
            ("fee and costs +2.5%/yr", dict(cost_infl=0.025, fee_infl=0.025)), ("costs +2.5%/yr, fee flat", dict(cost_infl=0.025)),
            ("no escalation", dict(escal=False)), ("ex bolt-ons", dict(bolt=False)), ("CP2 +0.00", dict(cp2x=0.0)), ("CP2 +0.85", dict(cp2x=0.85)),
            ("calibrated costs (basis kept)", dict(cost_mode="calibrated")), ("CP2 6-month delay", dict(delay=0.5)), ("CP2 12-month delay", dict(delay=1.0)),
            ("v9 accounting timing (D&A)", dict(da=M9.DA9, da_run=M9.DA_RUN))]
    S_ = {}
    for lab, kw in sens:
        a, b, c = value(L_CENTRAL, **kw), value(L_CENTRAL, roll=True, **kw), needed(**kw)
        S_[lab] = (a, b, c); L_.append(f"  {lab:<32} today {a:6.2f}  end-2028 {b:6.2f}  needs {c:5.2f}")
    # $138bn low end
    orig = M8.contracted_rev
    M8.contracted_rev = lambda y, con, fee, cp2x, on, _o=orig: _o(y, con, fee - (0.35 if y >= 2029 else 0.0), cp2x, on)
    lowend = (value(L_CENTRAL, cp2x=0.0), value(L_CENTRAL, roll=True, cp2x=0.0), needed(cp2x=0.0))
    M8.contracted_rev = orig
    L_.append(f"  $138bn low end (fees ~2.10, CP2 +0): today {lowend[0]:.2f}, end-2028 {lowend[1]:.2f}, needs {lowend[2]:.2f}")
    bonus = M9.bonus_upside()
    L_.append(f"  bonus depreciation upside +{bonus:.2f}")
    # management
    with contextlib.redirect_stdout(io.StringIO()):
        rows3, _ = series(3.0)
    op29 = rows3[2029]["open"]; mine3 = rows3[2029]["ebitda"] - op29 * (FUT[2029] - 3.0) / 1000; gap = 11.0 - mine3
    mg0, mg28, mgn = value(L_CENTRAL, uplift=gap), value(L_CENTRAL, roll=True, uplift=gap), needed(uplift=gap)
    L_.append(f"management: mine at $3 {mine3:.2f}; gap {gap:.2f}; today {mg0:.2f}, end-2028 {mg28:.2f}, needs {mgn:.2f}")
    # scenarios
    W = [("Bear: the wave lands ($2.50)", dict(L=2.50), 0.25), ("Base ($3.50)", dict(L=3.50), 0.45),
         ("Bull: replacement cost holds ($4.50)", dict(L=4.50), 0.20), ("Management's 2029 framework holds", dict(L=3.50, uplift=gap), 0.10)]
    sc = []; ev0 = ev28 = 0.0
    for lab, kw, w in W:
        L0 = kw.pop("L"); a, b = value(L0, **kw), value(L0, roll=True, **kw)
        tr = (b + 0.32) / PX - 1; sc.append((lab, w, a, b, tr)); ev0 += w * a; ev28 += w * b
        L_.append(f"  scenario {lab:<38} {w:.0%}: today {a:6.2f} end-2028 {b:6.2f} TR {tr:+.0%}")
    eq0 = sum(x[2] for x in sc) / 4; eq28 = sum(x[3] for x in sc) / 4
    L_.append(f"  weighted: today {ev0:.2f}, end-2028 {ev28:.2f}, 24-month TR {(ev28 + 0.32) / PX - 1:+.0%}; equal weights: today {eq0:.2f}, end-2028 {eq28:.2f}")
    # LRMC
    lr = []
    L_.append("LRMC at 8% after tax, VG opex 0.92: 20-year contract only | 35-year life (15 more years at the same fee) | 7%, 35-yr | no bonus, 35-yr")
    for r in read("lrmc_capex_comps.csv"):
        t = float(r["usd_per_tonne"])
        a, b, c, d = lrmc(t), lrmc(t, tail=15), lrmc(t, 0.07, tail=15), lrmc(t, tail=15, bonus=False)
        lr.append((r["project"], r["type"], t, a, b, c, d))
        L_.append(f"  {r['project']:<38} {t:6.0f}/t  {a:.2f} | {b:.2f} | {c:.2f} | {d:.2f}")
    # EPS readings and bridge
    from eps_path import DA as DA_OLD
    rows8 = M8.series(L_CENTRAL)[0]; nd8 = M8.net_debt_path(rows8)
    v8eps = {y: ((rows8[y]["ebitda"] - DA_OLD[y] - nd8[y]["pl_int"]) * (1 - TAX) - V.PREF - V.NCI) / SH for y in YEARS}
    pA = eps_path(); pB = eps_path(cip=CIP_V9, da=da_schedule(CIP_V9, "v9")[0], capi=M8.CAPI)
    L_.append("EPS (revenue reading, central): " + ", ".join(f"{y} {pA[y]['eps']:.2f}" for y in YEARS))
    L_.append("EPS (construction-cost reading, v9): " + ", ".join(f"{y} {pB[y]['eps']:.2f}" for y in YEARS))
    L_.append("reported EBITDA central: " + ", ".join(f"{y} {pA[y]['e_rep']:.2f}" for y in YEARS) + " | D&A " + ", ".join(f"{pA[y]['da']:.2f}" for y in YEARS))
    L_.append("FCF/ND central: " + ", ".join(f"{y} {pA[y]['fcf']:.2f}/{pA[y]['nd']:.1f}" for y in YEARS))
    need = (pA[2027]["eps"] - 1.00) * SH / (1 - TAX); op27 = V.open_tbtu[2027]
    L_.append(f"2027 bridge: cash-model v8 {v8eps[2027]:.2f} -> D&A and capitalized interest on v10 dates {pA[2027]['eps'] - v8eps[2027]:+.2f} -> v10 {pA[2027]['eps']:.2f}; consensus 1.00 needs {need:.2f}bn less pre-tax, i.e. all {op27:.0f} TBtu open at ~{FUT[2027] - need * 1000 / op27:.2f}; construction-cost reading {pB[2027]['eps']:.2f}")
    e26 = (V.bs["ebitda_guide_2026_low"] + V.bs["ebitda_guide_2026_high"]) / 2000; int26 = (933 + 2 * 489) / 1000
    eps26 = ((e26 - DA10[2026] - int26) * (1 - TAX) - V.PREF - V.NCI) / SH
    L_.append(f"2026 EPS {eps26:.2f}; P/E at 13.05: " + ", ".join(f"{y} {PX / pA[y]['eps']:.1f}x" for y in YEARS))
    # judgment audit (value today, base vs alternative)
    audit = [
        ("Long-run fee $3.50, not VG's 2010-26 median $5.19", "hurts VG", v0 - value(5.19)),
        ("Scenario weights 25/45/20/10, not equal", "hurts VG" if ev0 < eq0 else "helps VG", ev0 - eq0),
        ("Contract fees $2.45 + $0.40 CP2, not the $138bn low end", "helps VG", v0 - lowend[0]),
        ("Costs flat in dollars, not rising 2.5%/yr", "helps VG", v0 - S_["costs +2.5%/yr, fee flat"][0]),
        ("Fee and costs flat, not both rising 2.5%/yr", "hurts VG", v0 - S_["fee and costs +2.5%/yr"][0]),
        ("Plaquemines basis cost gone from 2029", "helps VG", v0 - S_["calibrated costs (basis kept)"][0]),
        ("Contract escalation included", "helps VG", v0 - S_["no escalation"][0]),
        ("Bolt-ons included before FID", "helps VG", v0 - S_["ex bolt-ons"][0]),
        ("Contracted 7% / open 10%, not CAPM-consistent 6% / 9%", "hurts VG", v0 - S_["CAPM-consistent 6% / 9%"][0]),
        ("Bonus depreciation left out", "hurts VG", -bonus),
        ("BP claim at half the low end, not zero", "hurts VG", -S.BP / SH),
        ("CP2 on schedule, no delay", "helps VG", v0 - S_["CP2 12-month delay"][0]),
    ]
    L_.append("judgment audit (value today, my choice minus the alternative):")
    for lab, d, x in audit:
        L_.append(f"  {lab:<58} {d:<9} {x:+.2f}")
    lo, hi = 0.0, 1.5
    for _ in range(60):
        m = (lo + hi) / 2; lo, hi = (m, hi) if value(3.5, flat_cost=m) > PX else (lo, m)
    L_.append(f"Henry Hub +$1 for good: {value(L_CENTRAL - 1.15) - v0:.2f}/sh; flat cost 0.92 at 3.50: {value(3.5, flat_cost=0.92):.2f}, needs {needed(flat_cost=0.92):.2f}; cost the price needs at 3.50: {m:.2f}; basis-cost removal worth {v0 - value(L_CENTRAL, cost_mode='calibrated'):.2f}")
    out = "\n".join(L_); print(out)
    open(os.path.join(RESULTS, "model_v10.txt"), "w").write(out + "\n")
    with open(os.path.join(RESULTS, "audit_v10.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["judgment", "direction", "value_today_effect"]); [w.writerow([a, b, f"{c:+.2f}"]) for a, b, c in audit]
    with open(os.path.join(RESULTS, "scenarios_v10.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["scenario", "weight", "today", "end2028", "tr24"]); [w.writerow([a, b, f"{c:.2f}", f"{d:.2f}", f"{e:.3f}"]) for a, b, c, d, e in sc]
    with open(os.path.join(RESULTS, "lrmc_v10.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["project", "type", "usd_t", "fee_20y", "fee_35y", "fee_35y_7pct", "fee_35y_no_bonus"]); [w.writerow([r[0], r[1], f"{r[2]:.0f}"] + [f"{x:.2f}" for x in r[3:]]) for r in lr]
    with open(os.path.join(RESULTS, "regimes_v10.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["regime", "ttf_mean", "ttf_median", "jkm_mean", "months"]); [w.writerow([a, f"{b:.2f}", f"{c:.2f}", "" if d is None else f"{d:.2f}", n]) for a, b, c, d, n in reg]
    with open(os.path.join(RESULTS, "eps_path_v10.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["year", "reported_ebitda", "da", "pl_interest", "eps_revenue_reading", "eps_construction_cost_reading", "fcf_after_div", "net_debt"])
        for y in YEARS: w.writerow([y] + [f"{x:.2f}" for x in (pA[y]["e_rep"], pA[y]["da"], pA[y]["pl_int"], pA[y]["eps"], pB[y]["eps"], pA[y]["fcf"], pA[y]["nd"])])
    with open(os.path.join(RESULTS, "payoff_v10.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["long_run_fee_from_2032", "today", "end2028", "today_real_flat", "today_management"])
        for i in range(17):
            x = i / 2; w.writerow([f"{x:.2f}"] + [f"{max(0, v):.2f}" for v in (value(x), value(x, roll=True), value(x, cost_infl=0.025, fee_infl=0.025), value(x, uplift=gap))])
