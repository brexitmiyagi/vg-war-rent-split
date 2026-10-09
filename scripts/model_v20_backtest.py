"""v20 backtest: does the supply-demand regime model explain history (2015-2025), and how do approvals respond to prices?

Data: data/lng_history_v20.csv (IGU World LNG Reports 2016-2026, GIIGNL 2015, EIA 3 Mar 2026; sources per cell)
      data/fred_ttf_hh_monthly.csv (fee on VG's formula, TTF basis: TTF - 1.15 x HH - 2)

Tests
1. Utilisation (trade / average nameplate) against the fee. If supply tightness showed up in utilisation, high
   utilisation years should be high-fee years.
2. Structural surplus: 84% of average nameplate against trend demand (log-linear trend of 2014-2025 trade), the same
   construction the forward model uses with Shell/GECF demand. Classify with the forward model's thresholds
   (glut > +5%, shortage < -2%) and compare with the fee regime each year actually paid.
3. Fee curve: least-squares line of fee on surplus over the years without an outside shock (2021-22 = Russia,
   a pipeline shock outside the LNG balance; 2026 = Hormuz, not in sample). Used by model_v20_supply.py.
4. Approvals: FIDs in year t against the fee in year t-1; and US SPAs (EIA) against US-led FIDs a year later.
"""
import os, csv, math
from common import RESULTS, DATA, HH_MULT, SHIP_REGAS

hist = {int(r["year"]): r for r in csv.DictReader(open(os.path.join(DATA, "lng_history_v20.csv")))}
m = list(csv.DictReader(open(os.path.join(DATA, "fred_ttf_hh_monthly.csv"))))
fee = {}
for y in range(2014, 2027):
    v = [float(r["ttf_imf_usd_mmbtu"]) - HH_MULT * float(r["henry_hub_usd_mmbtu"]) - SHIP_REGAS for r in m if int(r["month"][:4]) == y]
    fee[y] = sum(v) / len(v)
YRS = range(2015, 2026)
SHOCK = {2021, 2022}

def regime_actual(f):          # what the market paid, on the same fee bands the forward model uses
    return "glut" if f < 1.62 else ("shortage" if f > 9.0 else "balanced")

cap = {y: float(hist[y]["capacity_end_mtpa"]) for y in hist}
trade = {y: float(hist[y]["trade_mt"]) for y in hist}
avgcap = {y: (cap[y - 1] + cap[y]) / 2 for y in YRS}
util = {y: trade[y] / avgcap[y] for y in YRS}

ys = list(range(2014, 2026)); xm = sum(ys) / len(ys)
lm = sum(math.log(trade[y]) for y in ys) / len(ys)
g = sum((y - xm) * (math.log(trade[y]) - lm) for y in ys) / sum((y - xm) ** 2 for y in ys)
trend = {y: math.exp(lm + g * (y - xm)) for y in YRS}
surplus = {y: 0.84 * avgcap[y] / trend[y] - 1 for y in YRS}
def regime_model(s): return "glut" if s > 0.05 else ("shortage" if s < -0.02 else "balanced")

def corr(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))

L = ["1-2. Year by year: utilisation, structural surplus vs trend demand, the model's regime vs the regime paid"]
hits = n = 0
for y in YRS:
    rm, ra = regime_model(surplus[y]), regime_actual(fee[y])
    ok = rm == ra; n += 1; hits += ok
    L.append(f"   {y}: utilisation {util[y]:.1%} (IGU {hist[y]['igu_utilisation_pct'] or 'n/a'}) | surplus {surplus[y]:+.1%} -> {rm:<8} | fee {fee[y]:6.2f} -> {ra:<8} {'OK' if ok else 'MISS'}{' (outside shock)' if y in SHOCK else ''}")
L.append(f"   trend demand growth {math.exp(g) - 1:.1%}/yr. Regime hit rate {hits}/{n}; excluding the 2021-22 shock {sum(regime_model(surplus[y]) == regime_actual(fee[y]) for y in YRS if y not in SHOCK)}/{n - 2}")
L.append(f"   correlation with the fee: utilisation {corr([util[y] for y in YRS], [fee[y] for y in YRS]):+.2f}; surplus {corr([surplus[y] for y in YRS], [fee[y] for y in YRS]):+.2f} (all years), "
         f"{corr([surplus[y] for y in YRS if y not in SHOCK], [fee[y] for y in YRS if y not in SHOCK]):+.2f} (without 2021-22)")

xs = [surplus[y] for y in YRS if y not in SHOCK]; fs = [fee[y] for y in YRS if y not in SHOCK]
mx, mf = sum(xs) / len(xs), sum(fs) / len(fs)
k = sum((x - mx) * (f - mf) for x, f in zip(xs, fs)) / sum((x - mx) ** 2 for x in xs); c = mf - k * mx
res = [f - (c + k * x) for x, f in zip(xs, fs)]
r2 = 1 - sum(e * e for e in res) / sum((f - mf) ** 2 for f in fs)
se = math.sqrt(sum(e * e for e in res) / (len(xs) - 2))
L.append(f"3. Fee curve (no-shock years, n={len(xs)}): fee = {c:.2f} {k:+.1f} x surplus; R^2 {r2:.2f}; residual s.e. {se:.2f}")
L.append(f"   implied fee at a balanced market (0%): {c:.2f}; at +5%: {c + k * 0.05:.2f}; at +10%: {c + k * 0.10:.2f}; at -5%: {c - k * 0.05:.2f}")
with open(os.path.join(RESULTS, "fee_curve_v20.csv"), "w") as f:
    f.write("item,value\n"); f.write(f"intercept,{c:.4f}\nslope_per_unit_surplus,{k:.4f}\nr2,{r2:.4f}\nresid_se,{se:.4f}\nn,{len(xs)}\n")
with open(os.path.join(RESULTS, "backtest_v20.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["year", "avg_capacity", "trade", "utilisation", "trend_demand", "surplus", "model_regime", "fee_ttf_basis", "paid_regime", "outside_shock"])
    for y in YRS: w.writerow([y, round(avgcap[y], 1), trade[y], round(util[y], 4), round(trend[y], 1), round(surplus[y], 4), regime_model(surplus[y]), round(fee[y], 2), regime_actual(fee[y]), y in SHOCK])

fid = {y: float(hist[y]["fid_mtpa"]) for y in hist if hist[y]["fid_mtpa"]}
pairs = [(fee[y - 1], fid[y]) for y in range(2016, 2026)]
lo = [p[1] for p in pairs if p[0] < 3]; hi = [p[1] for p in pairs if p[0] >= 3]
flo = [p[0] for p in pairs if p[0] < 3]; fhi = [p[0] for p in pairs if p[0] >= 3]
slope = (sum(hi) / len(hi) - sum(lo) / len(lo)) / (sum(fhi) / len(fhi) - sum(flo) / len(flo))
icpt = sum(lo) / len(lo) - slope * sum(flo) / len(flo)
L.append("4. Approvals vs the previous year's fee (global FIDs, IGU):")
for y in range(2016, 2026): L.append(f"   {y}: FIDs {fid[y]:5.1f} Mtpa after a {y - 1} fee of {fee[y - 1]:6.2f}")
L.append(f"   after fees below $3: mean {sum(lo) / len(lo):.1f} Mtpa/yr (n={len(lo)}, average fee {sum(flo) / len(flo):.2f}); after fees of $3+: mean {sum(hi) / len(hi):.1f} (n={len(hi)}, average fee {sum(fhi) / len(fhi):.2f})")
L.append(f"   response used forward: FIDs = {icpt:.1f} + {slope:.2f} x last year's fee (bounded 0-70 Mtpa); correlation of FIDs with lagged fee {corr([p[0] for p in pairs], [p[1] for p in pairs]):+.2f} (lumpy: Qatar 2021, record 2019 at low fees)")
spa = {y: float(hist[y]["us_spa_mtpa"]) for y in hist if hist[y]["us_spa_mtpa"]}
L.append("   US contracts lead US approvals (EIA): SPAs 2021-25 " + ", ".join(f"{y} {v:.0f}" for y, v in spa.items()) + " Mtpa; the 2022 contracting record preceded the 2023 approvals, the 2024 DOE permit pause cut both, and 2025's 40 Mt preceded 2026's CP2 Phase 2, Commonwealth and Delfin approvals.")
with open(os.path.join(RESULTS, "fid_response_v20.csv"), "w") as f:
    f.write("item,value\n"); f.write(f"intercept,{icpt:.4f}\nslope_per_usd_fee,{slope:.4f}\nmean_after_low_fee,{sum(lo) / len(lo):.4f}\nmean_after_high_fee,{sum(hi) / len(hi):.4f}\n")
txt = "\n".join(L); print(txt); open(os.path.join(RESULTS, "backtest_v20.txt"), "w").write(txt + "\n")
