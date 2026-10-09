"""What is a 20-year contract worth to the buyer, as an option?

The buyer pays the fixed fee whether it lifts a cargo or not. It then lifts only when
the cargo is worth more than 115% of Henry Hub plus shipping, so each year it holds a
call on the liquefaction spread struck at zero, and the fixed fee is the premium.

I price that call with the Bachelier (normal) model, because the spread can go negative.
Forward = the CME-implied fee for each year (JKM less 115% of Henry Hub less 2).
Volatility = standard deviation of year-on-year changes in the annual-average spread,
2010-2025, using TTF (IMF) and Henry Hub (EIA) because that history is free. I show it
with and without 2021-2023, which dominate the sample.
ASSUMPTIONS: time to each year's midpoint from 6 Oct 2026; no discounting (I compare
it with an undiscounted fee); buyers' shipping and destination flexibility ignored.
"""
import os, math
from statistics import mean, pstdev, stdev
from common import read, RESULTS, annual_curve, fee_jkm, HH_MULT, SHIP_REGAS

rows = read("ttf_hh_monthly_2010_2025.csv")
ann = {}
for r in rows:
    y = int(r["month"][:4])
    ann.setdefault(y, []).append(float(r["ttf_imf_usd_mmbtu"]) - HH_MULT * float(r["henry_hub_usd_mmbtu"]) - SHIP_REGAS)
ann = {y: mean(v) for y, v in ann.items()}
ch_all = [ann[y] - ann[y - 1] for y in range(2011, 2026)]
ch_ex = [ann[y] - ann[y - 1] for y in range(2011, 2026) if y not in (2021, 2022, 2023, 2024)]
s_all, s_ex = stdev(ch_all), stdev(ch_ex)

def bach_call(F, K, sig, T):
    s = sig * math.sqrt(T)
    d = (F - K) / s
    N = 0.5 * (1 + math.erf(d / math.sqrt(2)))
    n = math.exp(-d * d / 2) / math.sqrt(2 * math.pi)
    return (F - K) * N + s * n

curve = annual_curve()
# market-implied: CME TTF options (futures-style margin) on 6 Oct 2026, nearest-strike calls,
# Apr-Oct 2027 expiries (the longest with a strike near the money). Lognormal vol x futures in $/MMBtu.
from common import EURUSD, MWH_PER_MMBTU
opt = [r for r in read("cme_ttf_options_atm_2026-10-06.csv") if r["contract"] in ("J27", "K27", "M27", "N27", "Q27", "U27", "V27")]
s_imp = mean(float(r["implied_vol_pct"]) / 100 * float(r["futures_eur_mwh"]) * EURUSD / MWH_PER_MMBTU for r in opt)
L = [f"annual spread (TTF basis) 2010-2025: " + ", ".join(f"{y}:{ann[y]:.1f}" for y in sorted(ann)),
     f"vol of yearly change: all years {s_all:.2f} $/MMBtu; excluding changes into 2021-2024 {s_ex:.2f}"]
L.append(f"market-implied normal vol (CME TTF options, Apr-Oct 2027 expiries, 6 Oct 2026): {s_imp:.2f} $/MMBtu per year; this is a monthly-contract vol, so it overstates the vol of an annual average")
L.append("year  forward fee  T   option value (all-years vol)  option value (calm vol)  option value (implied vol)  intrinsic")
vals = {}
for y in (2027, 2028, 2029, 2030, 2031):
    F = fee_jkm(curve[y]); T = (y + 0.5) - (2026 + 279 / 365)
    a, b, c = bach_call(F, 0.0, s_all, T), bach_call(F, 0.0, s_ex, T), bach_call(F, 0.0, s_imp, T)
    vals[y] = (F, a, b, c)
    L.append(f"{y}  {F:6.2f}  {T:4.2f}  {a:6.2f}  {b:6.2f}  {c:6.2f}  {max(F, 0):6.2f}")
avg_a = mean(v[1] for v in vals.values()); avg_b = mean(v[2] for v in vals.values()); avg_c = mean(v[3] for v in vals.values())
L.append(f"average 2027-2031 option value with market-implied vol: {avg_c:.2f}")
L.append(f"average 2027-2031 option value per MMBtu: {avg_a:.2f} (all-years vol), {avg_b:.2f} (calm vol); Calcasieu buyers pay a fixed fee of 2.36")
ph1 = 13.3 * 52
L.append(f"Plaquemines Phase 1 (13.3 MTPA = {ph1:.0f} TBtu/yr), 2027-2031, option value above a 2.36 fee: "
         f"{sum((v[1] - 2.36) * ph1 for v in vals.values()) / 1000:.1f} bn (all-years vol), {sum((v[2] - 2.36) * ph1 for v in vals.values()) / 1000:.1f} bn (calm vol)")
out = "\n".join(L); print(out)
open(os.path.join(RESULTS, "option_value.txt"), "w").write(out + "\n")
