# Who keeps the 2027 war spread from Venture Global's plants, priced off the futures curve.
from common import annual_curve, fee_jkm, read

c = annual_curve()[2027]
f27 = fee_jkm(c)
spa_fee = 2.36            # Calcasieu's contracted 2026 fee, slide 20. My proxy for SPA fees.
pre_war = 5.19            # Venture Global's own 2010-2026 median, slide 12
mm = 52                   # TBtu per MTPA per year, the factor Venture Global uses

buyers = {
    "Calcasieu third-party SPAs (10.0 MTPA)": 10.0 * mm,
    "Plaquemines Phase 1 SPAs (13.3 MTPA, full year)": 13.3 * mm,
    "Plaquemines Phase 2 SPAs (6.7 MTPA, from mid-2027)": 6.7 * mm * 0.5,
}
o = read("vg_outlook_slide23.csv")
open27 = next((float(r["ebitda_per_usd1_low_musd"]) + float(r["ebitda_per_usd1_high_musd"])) / 2
              for r in o if r["year"] == "2027")    # $m per $1 = TBtu left open

print(f"2027 curve fee (JKM - 1.15 x HH - 2): {f27:.2f}")
tot_b = 0
for k, v in buyers.items():
    print(f"  {k}: {v:.1f} TBtu -> {v*(f27-spa_fee)/1000:.2f} $bn above the contract fee")
    tot_b += v
print(f"SPA buyers total: {tot_b:.0f} TBtu, {tot_b*(f27-spa_fee)/1000:.2f} $bn above contract, "
      f"{tot_b*(f27-pre_war)/1000:.2f} $bn above the pre-war median")
print(f"Venture Global open volume: {open27:.0f} TBtu, {open27*(f27-spa_fee)/1000:.2f} $bn above contract, "
      f"{open27*(f27-pre_war)/1000:.2f} $bn above the pre-war median")
print(f"ratio buyers/VG: {tot_b/open27:.2f}")
