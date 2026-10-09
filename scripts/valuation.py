# A deliberately simple equity model. Everything Venture Global discloses comes from data/.
# Everything marked ASSUMPTION is my judgement call and is listed in the README.
LEGACY_NOTE = "LEGACY cross-check from an earlier version (v4-v6). The v7 numbers used in the piece are in results/model_v7.txt, waterfall.txt and pair_v7.txt.\n"
if __name__ == "__main__":
    print(LEGACY_NOTE, end="")
import csv, os
from common import annual_curve, fee_jkm, fee_ttf, read, RESULTS, PRICE_KEY

bs = {r["item"]: float(r["value"]) for r in read("vg_balance_sheet_2026-06-30.csv")}
out = {int(r["year"]): r for r in read("vg_outlook_slide23.csv")}
curve = annual_curve()

YEARS = range(2027, 2032)
TBTU_PER_CARGO = 3.7                       # Venture Global's own cargo assumption
vol = {y: (float(out[y]["cargos_low"]) + float(out[y]["cargos_high"])) / 2 * TBTU_PER_CARGO
       for y in (2026, 2027, 2028, 2029)}
vol[2030] = vol[2031] = 85 * 52            # ~85 MTPA "by the end of 2029" (slide 17)
open_tbtu = {y: (float(out[y]["ebitda_per_usd1_low_musd"]) + float(out[y]["ebitda_per_usd1_high_musd"])) / 2
             for y in (2026, 2027, 2028, 2029)}
# ASSUMPTION: once CP2 Phase 2 starts its SPAs (2030), 53 MTPA of third-party contracts are live
open_tbtu[2030] = 1900                     # part-year of CP2 Phase 2 SPAs
open_tbtu[2031] = vol[2031] - 53 * 52

# Calibrate one all-in cost per MMBtu so 2026 lands on the guidance midpoint:
# 91% contracted at $5.05 (slide 7), the open part at $13.00 (middle of $12.50-13.50).
g_mid = (bs["ebitda_guide_2026_low"] + bs["ebitda_guide_2026_high"]) / 2
c26 = vol[2026] - open_tbtu[2026]
COST = (c26 * 5.05 + open_tbtu[2026] * 13.00 - g_mid) / vol[2026]

CONTRACT_FEE = {2027: 3.00, 2028: 2.60, 2029: 2.45, 2030: 2.45, 2031: 2.45}   # ASSUMPTION
CAPEX = {2027: 10.0, 2028: 8.0, 2029: 5.0, 2030: 2.0, 2031: 1.0}             # ASSUMPTION, $bn
DEBT_COST = 0.063                           # ASSUMPTION, all-in on net debt
TAX = 0.19                                  # close to the 19.2% Q2 effective rate
PREF = bs["vglng_series_a_preferred_quarterly_dividend"] * 4 / 1000
NCI = 0.16                                  # 2026 NCI share of EBITDA, slide 16 midpoint
SHARES = bs["diluted_weighted_shares_q2"] / 1000
KE = 0.11                                   # ASSUMPTION: cost of equity for a levered, spread-exposed company. I show 9% to 13%.
# ASSUMPTION: net debt at end-2026. 30 Jun net debt plus H2 capex minus H2 cash earnings.
nd30jun = (bs["total_debt_outstanding"] - bs["cash_and_equivalents"]
           - bs["restricted_cash_current"] - bs["restricted_cash_noncurrent"]) / 1000
h2_ebitda = g_mid / 1000 - bs["h1_2026_adjusted_ebitda"] / 1000
h2_capex = (bs["capex_2026_guide"] - bs["capex_h1_2026"]) / 1000
ND0 = nd30jun + h2_capex - (h2_ebitda - nd30jun * DEBT_COST / 2 - 0.4)

def value(fee, terminal_fee, ke=KE, cost=None, capex=None):
    cost = COST if cost is None else cost
    capex = CAPEX if capex is None else capex
    nd = ND0
    path = []
    for i, y in enumerate(YEARS):
        ebitda = ((vol[y] - open_tbtu[y]) * CONTRACT_FEE[y] + open_tbtu[y] * fee[y] - cost * vol[y]) / 1000
        interest = nd * DEBT_COST
        taxable = max(0.0, ebitda - interest - (1.0 + 0.3 * i))   # rough tax depreciation
        fcfe = ebitda - interest - TAX * taxable - capex[y] - PREF - NCI
        nd -= fcfe                       # surplus pays debt down, deficits are borrowed
        path.append((y, ebitda, fcfe, nd))
    # steady state from 2032: no growth, no new projects valued
    e = ((vol[2031] - open_tbtu[2031]) * 2.45 + open_tbtu[2031] * terminal_fee - cost * vol[2031]) / 1000
    interest = nd * DEBT_COST
    cash = e - interest - TAX * max(0.0, e - interest - 2.4) - 1.0 - PREF - NCI
    equity = cash / ke / (1 + ke) ** 5
    return equity / SHARES, path

def implied_flat(price, **kw):
    lo, hi = 0.0, 20.0
    for _ in range(60):
        m = (lo + hi) / 2
        v, _ = value({y: m for y in YEARS}, m, **kw)
        lo, hi = (m, hi) if v < price else (lo, m)
    return (lo + hi) / 2

if __name__ == "__main__":
    price = bs[PRICE_KEY]
    print(f"calibrated all-in cost: {COST:.3f} $/MMBtu; net debt end-2026 (est): {ND0:.1f} $bn")
    jk = {y: fee_jkm(curve[y]) for y in YEARS}
    tt = {y: fee_ttf(curve[y]) for y in YEARS}
    med = 5.19
    scen = {
        "futures to 2031, then $3.00": (jk, 3.00),
        "TTF futures to 2031, then $3.00": (tt, 3.00),
        "futures to 2029, then VG median $5.19": ({**jk, 2030: med, 2031: med}, med),
        "VG median $5.19 every year": ({y: med for y in YEARS}, med),
        "futures to 2028, then pre-war $6.00": ({**jk, 2029: 6.0, 2030: 6.0, 2031: 6.0}, 6.0),
    }
    res = {}
    for name, (f, t) in scen.items():
        v, path = value(f, t)
        res[name] = v
        print(f"{name:<42} ${v:6.2f}/share   EBITDA path " +
              ", ".join(f"{y}:{e:.1f}" for y, e, _, _ in path))
    flat = implied_flat(price)
    print(f"flat fee implied by ${price}: {flat:.2f}")
    for ke in (0.09, 0.10, 0.11, 0.12, 0.13):
        print(f"  ke {ke:.0%}: implied flat fee {implied_flat(price, ke=ke):.2f}")
    for c in (0.95, COST, 1.35):
        print(f"  cost {c:.2f}: implied flat fee {implied_flat(price, cost=c):.2f}")
    for m in (0.7, 1.3):
        cx = {y: v * m for y, v in CAPEX.items()}
        print(f"  capex x{m}: implied flat fee {implied_flat(price, capex=cx):.2f}")
    # BP: half the low end of BP's own range, after tax. My judgement, not a forecast.
    bp = 3.7 * 0.5 * (1 - TAX) / SHARES
    bear = res["futures to 2031, then $3.00"] - bp
    base = res["futures to 2029, then VG median $5.19"] - bp
    bull = res["futures to 2028, then pre-war $6.00"] - bp
    target = 0.25 * bear + 0.5 * base + 0.25 * bull
    print(f"BP expected cost per share: {bp:.2f}")
    print(f"bear {bear:.2f}  base {base:.2f}  bull {bull:.2f}  weighted 25/50/25: {target:.2f}  "
          f"vs price {price}: {(target/price-1)*100:.0f}%")
    print(f"each $1 on the 2029 open fee, after tax, per share per year: "
          f"{open_tbtu[2029]*(1-TAX)/1000/SHARES:.2f}")
    print(f"BP claim per diluted share: {3.7/SHARES:.2f} to {6.0/SHARES:.2f}")
    with open(os.path.join(RESULTS, "valuation.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["case", "usd_per_share_before_bp"])
        for k, v in res.items(): w.writerow([k, round(v, 2)])
        w.writerow(["implied_flat_fee_at_price", round(flat, 2)])
        w.writerow(["bp_expected_per_share", round(bp, 2)])
        w.writerow(["weighted_target", round(target, 2)])
