"""v19 additions on top of model_v10.py (valuation unchanged unless stated):
1. What "shortage" means in the through-cycle test, and the test re-run without 2011-14.
2. CP2 cost overrun: +10% on the $30bn CP2 cost basis (+$3.0bn, spent 2027-28 in line with remaining CP2 capex,
   depreciated with the rest of CP2). Fees unchanged: CP2's contracts are fixed-fee.
3. New 20-year SPAs signed after the August deck: China Gas 0.5 MTPA and ConocoPhillips 1.0 MTPA, both from 2030
   (78 TBtu/yr). Fees not disclosed: modelled at the blended 2.45 contract fee, moved from open to contracted.
4. The supply model's fees (model_v19_supply.py) run through the valuation.
"""
import os, io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import valuation as V
    import model_v8 as M8
    import model_v10 as M
from common import RESULTS, read, HH_MULT, SHIP_REGAS

L = []
PX = M.PX

# 1. shortage definition
tt = {r["month"]: (float(r["ttf_imf_usd_mmbtu"]), float(r["henry_hub_usd_mmbtu"])) for r in read("fred_ttf_hh_monthly.csv")}
fee = {m: t - HH_MULT * h - SHIP_REGAS for m, (t, h) in tt.items() if 2011 <= int(m[:4]) <= 2026}
avg = lambda x: sum(x) / len(x)
need = M.needed()
def test(sample_years, short_years):
    f = {m: v for m, v in fee.items() if int(m[:4]) in sample_years}
    s = [v for m, v in f.items() if int(m[:4]) in short_years]
    w = [v for m, v in f.items() if 2015 <= int(m[:4]) <= 2020]
    o = [v for m, v in f.items() if int(m[:4]) not in short_years]
    S, W, O = avg(s), avg(w), avg(o)
    return len(f), len(s), len(s) / len(f), S, (need - W) / (S - W), (need - O) / (S - O), O
for lab, yrs, sy in (("2011-Sep 2026, shortage = 2011-14, 2021-22, 2026", range(2011, 2027), {2011, 2012, 2013, 2014, 2021, 2022, 2026}),
                     ("2015-Sep 2026, shortage = 2021-22, 2026 (2011-14 dropped)", range(2015, 2027), {2021, 2022, 2026})):
    n, k, sh, S, pw, po, O = test(set(yrs), sy)
    L.append(f"1. {lab}: {k}/{n} months = {sh:.0%} shortage, avg fee {S:.2f}; price ({need:.2f}) needs {pw:.0%} if other years are wave-like, {po:.0%} if like this sample's other years (avg {O:.2f})")
L.append("   definition: a shortage year = a calendar year in which a supply loss or demand shock pushed the market fee far above replacement cost "
         "(Fukushima and the oil-linked contract era 2011-14; Russia 2021-22; Hormuz 2026). All months of those years count.")

# helpers
def scen(**kw):
    with contextlib.redirect_stdout(io.StringIO()):
        rows3, _ = M.series(3.0)
    op29 = rows3[2029]["open"]; gap = 11.0 - (rows3[2029]["ebitda"] - op29 * (M8.FUT[2029] - 3.0) / 1000)
    W = [(2.50, 0.0, 0.25), (3.50, 0.0, 0.45), (4.50, 0.0, 0.20), (3.50, gap, 0.10)]
    return sum(w * M.value(l, uplift=u, **kw) for l, u, w in W), sum(w * M.value(l, roll=True, uplift=u, **kw) for l, u, w in W)
b0, b28, bw0, bw28, bn = M.value(3.5), M.value(3.5, roll=True), *scen(), need
L.append(f"base: today {b0:.2f}, end-2028 {b28:.2f}, weighted {bw0:.2f}/{bw28:.2f}, fee needed {bn:.2f}")

# 2. CP2 overrun
cap0, cost0, da0 = dict(V.CAPEX), M.CP2_COST, (M.DA10, M.DA_RUN10)
for pct in (0.10, 0.20):
    extra = pct * cost0
    V.CAPEX[2027] = cap0[2027] + 0.6 * extra; V.CAPEX[2028] = cap0[2028] + 0.4 * extra
    M.CP2_COST = cost0 + extra; M.DA10, M.DA_RUN10 = M.da_schedule()
    v0, v28, w0, w28, n2 = M.value(3.5), M.value(3.5, roll=True), *scen(), M.needed()
    L.append(f"2. CP2 +{pct:.0%} (+{extra:.1f}bn): today {v0:.2f} ({v0 - b0:+.2f}), end-2028 {v28:.2f} ({v28 - b28:+.2f}), weighted end-2028 {w28:.2f} ({w28 - bw28:+.2f}), fee needed {n2:.2f} ({n2 - bn:+.2f})")
    V.CAPEX.clear(); V.CAPEX.update(cap0); M.CP2_COST = cost0; M.DA10, M.DA_RUN10 = da0

# 3. new SPAs
op0 = dict(V.open_tbtu)
for y in (2030, 2031): V.open_tbtu[y] = op0[y] - 78.0
s0, s28, sw0, sw28, sn = M.value(3.5), M.value(3.5, roll=True), *scen(), M.needed()
L.append(f"3. +1.5 MTPA contracted from 2030 at 2.45: today {s0:.2f} ({s0 - b0:+.2f}), end-2028 {s28:.2f} ({s28 - b28:+.2f}), weighted end-2028 {sw28:.2f} ({sw28 - bw28:+.2f}), fee needed {sn:.2f} ({sn - bn:+.2f})")
L.append(f"   open share of 2031 volume: {op0[2031] / V.vol[2031]:.1%} -> {V.open_tbtu[2031] / V.vol[2031]:.1%}")
V.open_tbtu.clear(); V.open_tbtu.update(op0)

# 4. supply-model fees through the valuation (read from results/supply_summary_v19.csv)
import csv
sm = {r["item"]: float(r["value"]) for r in csv.DictReader(open(os.path.join(RESULTS, "supply_summary_v19.csv")))}
for lab, f in (("FIDs at the 2016-20 pace or slower, midpoint demand: market balanced at replacement cost", 3.90),
               ("history-paced FIDs, mean of all cases", sm["mean_fee_central"]),
               ("same, with 2011-26-rate shocks on top (upper bound)", sm["mean_fee_shocks"])):
    L.append(f"4. long-run fee {f:.2f} ({lab}): today {M.value(f):.2f}, end-2028 {M.value(f, roll=True):.2f}")
txt = "\n".join(L); print(txt); open(os.path.join(RESULTS, "model_v19_addons.txt"), "w").write(txt + "\n")
