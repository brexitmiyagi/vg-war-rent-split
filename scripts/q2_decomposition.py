# Where Venture Global's Q2 2026 operating income came from, by plant.
from common import read

rows = [r for r in read("vg_segments_q2_2026.csv") if r["period"] == "Q2 2026"]
total = sum(float(r["income_from_operations_musd"]) for r in rows)
print(f"Q2 2026 income from operations: {total:.0f} $m")
for r in rows:
    oi = float(r["income_from_operations_musd"])
    print(f"  {r['segment']:<30} {oi:>7.0f}  {oi/total*100:6.1f}% of total")
plaq = next(r for r in rows if r["segment"] == "Plaquemines")
calc = next(r for r in rows if r["segment"] == "Calcasieu")
for name, r in (("Plaquemines", plaq), ("Calcasieu", calc)):
    ebitda = float(r["income_from_operations_musd"]) + float(r["da_musd"])
    print(f"  {name} segment EBITDA (op income + D&A): {ebitda:.0f} $m")

fees = {r["item"]: float(r["value_usd_mmbtu"]) for r in read("vg_fees.csv")}
gap = fees["Plaquemines fee Q2 2026"] - fees["Calcasieu fee Q2 2026"]
print(f"Q2 fee gap, commissioning Plaquemines vs contracted Calcasieu: {gap:.2f} $/MMBtu")
ph1_q_tbtu = 13.3 * 52 / 4
print(f"Phase 1 SPA volume per quarter: {ph1_q_tbtu:.1f} TBtu -> at the Q2 gap that is "
      f"{ph1_q_tbtu*gap/1000:.2f} $bn a quarter moving to Phase 1 buyers at COD")
h1 = [r for r in read("vg_segments_q2_2026.csv") if r["period"] in ("H1 2026", "H1 2025")]
for seg in ("Calcasieu",):
    a = [float(r["income_from_operations_musd"]) for r in h1 if r["segment"] == seg]
    print(f"  {seg} H1 op income 2026 vs 2025: {a[0]:.0f} vs {a[1]:.0f} ({(a[0]/a[1]-1)*100:.0f}%)")
