# What the futures curve says a spot US liquefaction fee is worth, year by year.
import csv, os
from common import annual_curve, fee_jkm, fee_ttf, RESULTS

curve = annual_curve()
rows = []
for y in sorted(curve):
    c = curve[y]
    rows.append([y, round(c["jkm"], 3), round(c["ttf"], 2), round(c["hh"], 3),
                 round(fee_jkm(c), 2), round(fee_ttf(c), 2)])
    print(f"{y}: JKM {c['jkm']:.2f}  TTF {c['ttf']:.2f} EUR  HH {c['hh']:.3f}  "
          f"fee (JKM) {fee_jkm(c):.2f}  fee (TTF) {fee_ttf(c):.2f}")
print("2026 row covers Nov and Dec only.")
with open(os.path.join(RESULTS, "curve_fees.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["year", "jkm_usd", "ttf_eur_mwh", "henry_hub_usd", "fee_jkm_method", "fee_ttf_method"])
    w.writerows(rows)
