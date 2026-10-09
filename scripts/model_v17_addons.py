"""v17: fundamentals and framing checks (valuation core unchanged from model_v10.py).
1. LNG balance 2025-2040: committed supply (existing + under construction) vs two published demand paths.
2. What the balance implies for the long-run fee: two fee paths and their flat equivalents, valued in the model.
3. Contract fees are not forecasts: the Vitol five-year fee against the 2027 strip at signing.
4. Merchant premium history (Argus) against my regime table.
5. Publication-day sensitivity: the fee the price needs at the 8 Oct close.
"""
import os, io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import model_v10 as M
from common import RESULTS
L = []
# 1. balance
base25, supply30 = 437.0, 437.0 + 180.0          # IGU 2025 trade; Shell ~180 Mt new supply by 2030 (IEA ~184 Mt)
def supply(y):
    if y <= 2025: return base25
    if y >= 2030: return supply30
    return base25 + (supply30 - base25) * (y - 2025) / 5
def shell(y):   # straight line 422 (2025) -> 700 (2050)
    return 422 + (700 - 422) * (y - 2025) / 25
def gecf(y):    # straight line 406 (2024) -> 700 (2035) -> 785 (2040)
    return 406 + (700 - 406) * (y - 2024) / 11 if y <= 2035 else 700 + (785 - 700) * (y - 2035) / 5
war = {2026: 55, 2027: 30, 2028: 10, 2029: 5, 2030: 3}   # ~103 Mt cumulative (IEA 140 bcm), front-loaded (my split)
L.append("1. Committed supply (2025 trade + ~180 Mt new by 2030, less IEA war losses) vs demand paths, Mt and surplus % of demand:")
rows = []
for y in (2026, 2027, 2028, 2030, 2032, 2035, 2038, 2040):
    s = supply(y) - war.get(y, 0)
    a, b = shell(y), gecf(y)
    rows.append((y, s, a, b))
    L.append(f"   {y}: supply {s:5.0f} | Shell path {a:5.0f} ({s / a - 1:+.0%}) | GECF path {b:5.0f} ({s / b - 1:+.0%})")
open(os.path.join(RESULTS, "lng_balance_v17.csv"), "w").write("year,committed_supply,shell_demand,gecf_demand\n" + "\n".join(f"{y},{s:.0f},{a:.0f},{b:.0f}" for y, s, a, b in rows) + "\n")
L.append("   committed supply exceeds both demand paths through 2030; GECF's path overtakes it around 2032-33, Shell's not before ~2045 (supply held flat after 2030, no plant retirements)")
# 2. fee paths -> flat equivalents at 10% over 2032-2049
yrs = range(2032, 2050)
def flat_eq(path):
    w = [(1.10) ** -(y - 2032) for y in yrs]
    return sum(path(y) * x for y, x in zip(yrs, w)) / sum(w)
paths = {"glut lasts (Shell path): 2.75 to 2034, 3.25 after": lambda y: 2.75 if y < 2035 else 3.25,
         "tight by mid-2030s (GECF path): 3.00 to 2034, 4.00 after": lambda y: 3.00 if y < 2035 else 4.00}
L.append("2. Fee paths implied by the two balances, flat equivalent at 10%, and value:")
eqs = []
for k, f in paths.items():
    e = flat_eq(f); eqs.append(e)
    L.append(f"   {k}: flat-equivalent {e:.2f} -> value today {M.value(e):.2f}, end-2028 {M.value(e, roll=True):.2f}")
avg = sum(eqs) / 2
L.append(f"   average of the two {avg:.2f} vs my 3.50 -> value today {M.value(avg):.2f}, end-2028 {M.value(avg, roll=True):.2f}")
# 3. Vitol vs strip at signing
jkm27, hh27 = 15.125, 3.838
fee27 = jkm27 - 1.15 * hh27 - 2.0
L.append(f"3. Vitol five-year (signed Mar 2026) at ~$3.15 on a 115% basis vs the 2027 strip at signing: JKM {jkm27} - 1.15 x HH {hh27} - 2 = {fee27:.2f}; "
         f"Oct 7 curve 2027-30 average fee {(15.41 + 8.03 + 5.12 + 3.80) / 4:.2f}. Contract fees sit far below the strip: they price volume and financing, not expected spot.")
# 4. Argus merchant premium
for yr, prem in ((2023, 5.37), (2024, 4.63), (2025, 4.11)):
    L.append(f"4. {yr}: Gulf Coast spot fob over a 115% HH + $3 contract: +{prem:.2f} -> implied spot fee ~{3 + prem:.2f}")
L.append("   my 2023-25 regime average on VG's formula: 6.73 (TTF) to 7.26 (JKM) - consistent; the 2015-20 wave averaged 0.45 / 1.62")
# 5. publication-day
for px in (13.05, 13.29):
    lo, hi = -5.0, 30.0
    for _ in range(80):
        m = (lo + hi) / 2; lo, hi = (m, hi) if M.value(m) < px else (lo, m)
    L.append(f"5. at {px:.2f}: fee needed from 2032 {m:.2f}; base end-2028 TR {(M.value(3.5, roll=True) + 0.32) / px - 1:+.0%}")
out = "\n".join(L); print(out); open(os.path.join(RESULTS, "model_v17_addons.txt"), "w").write(out + "\n")
