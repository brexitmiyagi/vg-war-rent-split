"""What the spread did after the last LNG supply wave, and how big the next one is.

Spread = TTF (IMF, via FRED) less 115% of Henry Hub (EIA) less $2, annual averages.
TTF is used because JKM monthly history is not free. Venture Global's own JKM-based series
(slide 12, Jan 2010 to Jun 2026) has a median of 5.19; this TTF series has a lower median
over 2010-2025, so treat the TTF levels as a floor for what a JKM seller earned.
Supply figures are from IEA and IGU (data/lng_supply_wave.csv). The bcm-to-Mt conversion is mine.
"""
import os
from statistics import mean, median
from common import read, RESULTS, HH_MULT, SHIP_REGAS, jkm_monthly

ann = {}
for r in read("ttf_hh_monthly_2010_2025.csv"):
    ann.setdefault(int(r["month"][:4]), []).append(
        float(r["ttf_imf_usd_mmbtu"]) - HH_MULT * float(r["henry_hub_usd_mmbtu"]) - SHIP_REGAS)
ann = {y: mean(v) for y, v in ann.items()}
J = jkm_monthly()
hh = {r["month"]: float(r["henry_hub_usd_mmbtu"]) for r in read("ttf_hh_monthly_2010_2025.csv")}
jann = {}
for mth, v in J.items():
    if mth in hh:
        jann.setdefault(int(mth[:4]), []).append(v - HH_MULT * hh[mth] - SHIP_REGAS)
jann = {y: mean(v) for y, v in jann.items() if len(v) == 12}
w = {r["item"]: float(r["value"]) for r in read("lng_supply_wave.csv")}
L = ["annual TTF-basis fee: " + ", ".join(f"{y} {v:.2f}" for y, v in sorted(ann.items()))]
L.append(f"2016-2019 average (before Covid): {mean(ann[y] for y in range(2016, 2020)):.2f}; 2016-2020: {mean(ann[y] for y in range(2016, 2021)):.2f}")
L.append(f"2010-2025 median on TTF basis: {median(ann.values()):.2f} (VG's JKM-basis median, slide 12: 5.19)")
L.append("annual JKM-basis fee (IMF Asia LNG spot series, 2017 on): " + ", ".join(f"{y} {v:.2f}" for y, v in sorted(jann.items())))
L.append(f"JKM basis 2017-2019 average (before Covid): {mean(jann[y] for y in (2017, 2018, 2019)):.2f}; 2017-2020: {mean(jann[y] for y in range(2017, 2021)):.2f}")
L.append(f"JKM basis 2017-2025 median: {median(jann.values()):.2f}")
mt = w["net_lng_supply_increase_by_2030"] / w["bcm_per_mt_lng"]
L.append(f"IEA net LNG supply increase by 2030: {w['net_lng_supply_increase_by_2030']:.0f} bcm/yr = about {mt:.0f} Mt/yr, "
         f"{mt / w['global_lng_trade_2025']:.0%} of 2025 global LNG trade ({w['global_lng_trade_2025']:.0f} Mt, IGU)")
L.append(f"IEA war losses 2026-2030: {w['war_supply_losses_2026_2030']:.0f} bcm cumulative, 15% of new supply, concentrated in 2026-27")
out = "\n".join(L); print(out)
open(os.path.join(RESULTS, "last_wave.txt"), "w").write(out + "\n")
