"""What Venture Global sold to Vitol in the middle of the war.

Traders told Platts the five-year Vitol deal is priced at 119% of Henry Hub plus
2.80 to 3.20. Venture Global doesn't publish the fee, so treat this as reported, not filed.
I value the buyer's side at the 2 Oct 2026 CME curve for the four full calendar
years 2027 to 2030 (2026 and 2031 are partial years and I leave them out).
"""
from common import annual_curve, RESULTS, SHIP_REGAS
import os

TBTU_PER_MT = 52.0       # same conversion as valuation.py
MTPA = 1.7
HH_MULT_VITOL = 1.19
lines = []
curve = annual_curve()
for fee in (2.80, 3.00, 3.20):
    total = 0.0
    rows = []
    for y in (2027, 2028, 2029, 2030):
        c = curve[y]
        spot_fee = c["jkm"] - HH_MULT_VITOL * c["hh"] - SHIP_REGAS
        gain = (spot_fee - fee) * MTPA * TBTU_PER_MT / 1000  # $bn
        total += gain
        rows.append(f"  {y}: spot fee on a 119% HH basis {spot_fee:5.2f}, buyer keeps {gain:5.2f} bn")
    lines.append(f"Vitol fee {fee:.2f}: buyer keeps {total:.2f} bn over 2027-2030 at the curve")
    lines += rows
out = "\n".join(lines)
print(out)
open(os.path.join(RESULTS, "firm_start_vitol.txt"), "w").write(out + "\n")
