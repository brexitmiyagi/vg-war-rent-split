"""v20 valuation add-ons (valuation core unchanged: model_v10.py).
1. The supply model's long-run fees run through the valuation (results/supply_summary_v20.csv, supply_v20.csv).
2. Prolonged Hormuz: the supply model's extra fee in 2027-31 versus its own central path, added to the CME strip
   (results/model_v20_supply.txt section D); long-run fee unchanged at $3.50 because faster approvals offset it.
"""
import os, io, csv, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import model_v8 as M8
    import model_v10 as M
from common import RESULTS

sm = {r["item"]: float(r["value"]) for r in csv.DictReader(open(os.path.join(RESULTS, "supply_summary_v20.csv")))}
sv = list(csv.DictReader(open(os.path.join(RESULTS, "supply_v20.csv"))))
L = []
b0, b28 = M.value(3.5), M.value(3.5, roll=True)
L.append(f"base $3.50: today {b0:.2f}, end-2028 {b28:.2f}")
for lab, f in (("supply model mean, all cases, with shocks", sm["mean_fee_central"]),
               ("supply model, no shocks", sm["mean_fee_noshock_central"]),
               ("history-fitted curve without market calibration", sm["hist_only_mean"])):
    L.append(f"1. {lab}: fee {f:.2f} -> today {M.value(f):.2f}, end-2028 {M.value(f, roll=True):.2f}")
for name in ("Shell", "midpoint", "GECF"):
    rows = [r for r in sv if r["scenario"] == "central" and r["demand"] == name]
    f = sum(float(r["flat_fee_mean"]) for r in rows) / len(rows)
    L.append(f"   by demand path {name:<8}: mean fee {f:.2f} -> end-2028 {M.value(f, roll=True):.2f}; P(>=4.49) {sum(float(r['p_fee_ge_4.49']) for r in rows) / len(rows):.0%}")

# 2. Hormuz: model's scenario increment over its own central path, applied to the futures
inc = {y: sm[f"hormuz_fee_{y}"] - sm[f"central_fee_{y}"] for y in range(2027, 2032)}
fut0 = dict(M8.FUT)
try:
    for y in range(2027, 2032): M8.FUT[y] = fut0[y] + inc[y]
    h0, h28, hn = M.value(3.5), M.value(3.5, roll=True), M.needed()
finally:
    M8.FUT.clear(); M8.FUT.update(fut0)
L.append("2. Prolonged Hormuz: extra fee vs the model's central path " + " ".join(f"{y} {inc[y]:+.2f}" for y in range(2027, 2032)))
L.append(f"   value today {h0:.2f} ({h0 - b0:+.2f}), end-2028 {h28:.2f} ({h28 - b28:+.2f}); fee needed from 2032 {hn:.2f}")
try:
    M8.FUT[2027] = 28.14; M8.FUT[2028] = max(fut0[2028] + inc[2028], 15.41)
    for y in (2029, 2030, 2031): M8.FUT[y] = fut0[y] + inc[y]
    s0, s28 = M.value(3.5), M.value(3.5, roll=True)
finally:
    M8.FUT.clear(); M8.FUT.update(fut0)
L.append(f"   severe variant (2027 pays 2022's $28.14, 2028 at least 2027's strip $15.41): today {s0:.2f}, end-2028 {s28:.2f}")
txt = "\n".join(L); print(txt); open(os.path.join(RESULTS, "model_v20_addons.txt"), "w").write(txt + "\n")
