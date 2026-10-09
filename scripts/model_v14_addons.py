"""v14: primary-source corrections and three new disclosures (valuation core unchanged from model_v10.py).
1. LRMC on corrected replacement-cost comps (data/lrmc_capex_comps_v14.csv): Rio Grande ex-financing ($847/t),
   Commonwealth at $13bn ($1,368/t), Corpus Christi Trains 8-9 dropped (no cost in Cheniere's FID release).
2. 2027-28 contracted fee ($3.00 / $2.60, my assumption; VG does not disclose it): EPS and value per $1.
3. Peer multiple recomputed from primary inputs: EV / 2026 guided Adjusted EBITDA, VG vs Cheniere.
4. Cheniere's exposure to the long-run fee on "90% or more" contracted through the mid-2030s.
"""
import os, io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import model_v10 as M
    import valuation as V
from common import RESULTS, read
L = []
# 1. LRMC
comps = read("lrmc_capex_comps_v14.csv")
L.append("LRMC at 8% after tax, VG opex 0.92, 21% tax, bonus depreciation: 20-year | 35-year | 35-year at 7% | 35-year no bonus")
rows = []
for r in comps:
    t = float(r["usd_per_tonne"])
    a, b, c, d = M.lrmc(t), M.lrmc(t, tail=15), M.lrmc(t, hurdle=0.07, tail=15), M.lrmc(t, tail=15, bonus=False)
    rows.append((r["project"], t, a, b, c, d)); L.append(f"  {r['project']:<40} {t:>5.0f}/t  {a:.2f} | {b:.2f} | {c:.2f} | {d:.2f}")
g = [x for x in rows if "Commonwealth" not in x[0] and "VG" not in x[0]]
L.append(f"  three greenfield comps ex Commonwealth, 35-year: {min(x[3] for x in g):.2f}-{max(x[3] for x in g):.2f}; 20-year: {min(x[2] for x in g):.2f}-{max(x[2] for x in g):.2f}")
with open(os.path.join(RESULTS, "lrmc_v14.csv"), "w") as f:
    f.write("project,usd_t,fee_20y,fee_35y,fee_35y_7pct,fee_35y_no_bonus\n")
    for p, t, a, b, c, d in rows: f.write(f"{p},{t:.0f},{a:.2f},{b:.2f},{c:.2f},{d:.2f}\n")
# 2. contracted fee 2027-28
base_fee = dict(V.CONTRACT_FEE); e0 = M.eps_path(); v0 = M.value(3.50); w0 = M.value(3.50, roll=True)
for dlt in (-1.0, 1.0):
    V.CONTRACT_FEE[2027] = base_fee[2027] + dlt; V.CONTRACT_FEE[2028] = base_fee[2028] + dlt
    e1 = M.eps_path(); v1 = M.value(3.50); w1 = M.value(3.50, roll=True)
    L.append(f"contracted fee 2027-28 {dlt:+.0f} ({V.CONTRACT_FEE[2027]:.2f}/{V.CONTRACT_FEE[2028]:.2f}): EPS 2027 {e1[2027]['eps']:.2f} ({e1[2027]['eps']-e0[2027]['eps']:+.2f}), 2028 {e1[2028]['eps']:.2f} ({e1[2028]['eps']-e0[2028]['eps']:+.2f}); value today {v1:.2f} ({v1-v0:+.2f}), end-2028 {w1:.2f} ({w1-w0:+.2f})")
    V.CONTRACT_FEE.update(base_fee)
# alternative: contracted 2027-28 at the long-run contract average 2.45
V.CONTRACT_FEE[2027] = V.CONTRACT_FEE[2028] = 2.45
e2 = M.eps_path(); v2 = M.value(3.50); V.CONTRACT_FEE.update(base_fee)
L.append(f"audit: 2027-28 contracted at $3.00/$2.60, not the $2.45 long-run contract average: value today {v0 - v2:+.2f}, EPS 2027 {e0[2027]['eps'] - e2[2027]['eps']:+.2f}")
# 3. peer multiple (7 Oct closes; balance sheets 30 Jun 2026)
vg_px, lng_px, cqp_px = 13.05, 272.20, 63.44
vg_mcap = 2.643 * vg_px; vg_nd = 42.386 - 3.120 - 0.068 - 1.402; vg_pref = 3.0; vg_nci = 3.507
vg_ev = vg_mcap + vg_nd + vg_pref + vg_nci; vg_e = 8.9
lng_mcap = 206.534 * lng_px / 1000 * 1000 / 1000; lng_mcap = 206.534e6 * lng_px / 1e9
lng_nd = (1.411 + 22.632) - (1.099 + 0.420); lng_nci = (484.058 - 239.9) * cqp_px / 1000
lng_ev = lng_mcap + lng_nd + lng_nci; lng_e = 8.15
L.append(f"VG: diluted mkt cap {vg_mcap:.2f} + net debt {vg_nd:.2f} + preferred {vg_pref:.1f} + NCI (book) {vg_nci:.2f} = EV {vg_ev:.1f}bn; 2026 guide mid {vg_e} -> {vg_ev/vg_e:.2f}x")
L.append(f"Cheniere: mkt cap {lng_mcap:.2f} + net debt {lng_nd:.2f} + CQP units held by others at market {lng_nci:.2f} = EV {lng_ev:.1f}bn; 2026 guide mid {lng_e} -> {lng_ev/lng_e:.2f}x")
eq_at_lng = (lng_ev / lng_e * vg_e - vg_nd - vg_pref - vg_nci) / 2.643
L.append(f"VG at Cheniere's multiple on 2026 guidance: {eq_at_lng:.2f}/share; on my 2028 EBITDA {e0[2028]['e_rep']:.2f}bn the same EV is {vg_ev/e0[2028]['e_rep']:.2f}x, on my 2031 {e0[2031]['e_rep']:.2f}bn {vg_ev/e0[2031]['e_rep']:.2f}x")
# 4. Cheniere exposure
for share in (0.90, 0.95):
    per = (1 - share) * 53.5 * 52 / 206.534 * 1.0 * (1 - 0.21) / 0.10
    L.append(f"Cheniere at {share:.0%} contracted: ~{per:.2f}/share per $1 of long-run margin ({per/lng_px:.1%} of price) [perpetuity at 10%, 21% tax, 53.5 Mt]")
out = "\n".join(L); print(out); open(os.path.join(RESULTS, "model_v14_addons.txt"), "w").write(out + "\n")
# 5. pair payoff with Cheniere's fee exposure at 90% contracted (10.64/sh) vs 95% (5.32/sh)
PX = M.PX; gap = 3.078; lng24 = (1 + 0.0528 + 0.31 * 0.042) ** 2 - 1
cases = [("bear", 2.50, 0.0, 0.25), ("base", 3.50, 0.0, 0.45), ("bull", 4.50, 0.0, 0.20), ("management", 3.50, gap, 0.10)]
L2 = []
for ch_per in (5.32, 10.64):
    res = []; ev = 0.0
    for c, l, u, w in cases:
        vg = (M.value(l, roll=True, uplift=u) + 0.32) / PX - 1
        lng = lng24 + (l - 3.5) * ch_per / 272.20
        p = -vg + 1.51 * lng - 0.0082; ev += w * p; res.append(f"{c} {p:+.0%}")
    L2.append(f"pair per $1 short at Cheniere exposure {ch_per}/sh: " + ", ".join(res) + f"; weighted {ev:+.1%}")
print("\n".join(L2)); open(os.path.join(RESULTS, "model_v14_addons.txt"), "a").write("\n".join(L2) + "\n")
