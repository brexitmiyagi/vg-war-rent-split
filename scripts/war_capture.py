"""Does Venture Global's realized fee follow the spot market, or the market as it was
when the cargo was sold?

Spot fee = JKM less 115% of Henry Hub less 2 dollars, Venture Global's slide-12 formula.
JKM here is the IMF's Asia LNG price (PNGASJP), a daily-averaged spot series from 2017 that
tracks JKM (IMF Q2 2026 average 17.29 against the IEA's published JKM of about 17.5), through
August 2026; September 2026 is my estimate from JOGMEC's weekly JKM assessments (see
data/jkm_imf_monthly.csv). Henry Hub is EIA through August and the World Bank for September.
Run with BASIS=ttf to get the earlier TTF version (TTF in place of JKM) as a cross-check.

Venture Global restated its fee measure in 2026. Everything compared here is on the
current basis (the 2026 decks and the 2026 8-Ks, which match the decks). The 2025 8-K
numbers are printed for reference only.

Plaquemines Q3 2026 isn't published by plant any more. I back it out of the company
figure using Calcasieu's own run-rate (2.28 in Q1 and 2.44 in Q2), so it is a range.
"""
import os
from statistics import mean
from common import read, RESULTS, HH_MULT, SHIP_REGAS, jkm_monthly
BASIS = os.environ.get("BASIS", "jkm")
JKM = jkm_monthly()

m = {r["month"]: r for r in read("fred_ttf_hh_monthly.csv")}
f = {r["item"]: float(r["value"]) for r in read("vg_fee_history.csv")}

def qspot(y, q):
    ms = [f"{y}-{mm:02d}" for mm in range(3 * q - 2, 3 * q + 1)]
    ttf = mean((JKM[x] if BASIS == "jkm" else float(m[x]["ttf_imf_usd_mmbtu"])) for x in ms)
    hh = mean(float(m[x]["henry_hub_usd_mmbtu"]) for x in ms)
    return ttf - HH_MULT * hh - SHIP_REGAS

def prev(y, q):
    return (y - 1, 4) if q == 1 else (y, q - 1)

def stats(rows):
    xs_s = [qspot(*k) for k, _ in rows]; xs_p = [qspot(*prev(*k)) for k, _ in rows]; ys = [v for _, v in rows]
    def cs(xs):
        mx, my = mean(xs), mean(ys)
        cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
        vx = sum((a - mx) ** 2 for a in xs); vy = sum((b - my) ** 2 for b in ys)
        return cov / (vx * vy) ** 0.5, cov / vx
    return cs(xs_s), cs(xs_p), mean(abs(b - a) for a, b in zip(xs_s, ys)), mean(abs(b - a) for a, b in zip(xs_p, ys))

def plaq_q3_2026(calc_fee):
    tot = f["company_q3_2026"] * f["company_q3_2026_tbtu"]
    return (tot - calc_fee * f["calcasieu_q3_2026_tbtu"]) / f["plaq_q3_2026_tbtu"]

L = [f"spot basis: {BASIS.upper()}"]
# check the back-out method on Q2 2026, where the deck gives Plaquemines directly
q2 = (f["company_q2_2026_new"] * f["company_q2_2026_tbtu"] - f["calcasieu_q2_2026_new"] * f["calcasieu_q2_2026_tbtu"]) / f["plaq_q2_2026_tbtu"]
L.append(f"method check, Q2 2026: backed-out Plaquemines {q2:.2f} vs deck {f['plaq_q2_2026_new']:.2f}")
p3_lo, p3_hi = plaq_q3_2026(f["calcasieu_q2_2026_new"]), plaq_q3_2026(f["calcasieu_q1_2026_new"])
p3 = (p3_lo + p3_hi) / 2
L.append(f"Plaquemines Q3 2026 backed out: {p3_lo:.2f} to {p3_hi:.2f}, using {p3:.2f}")

company = [((2025, 1), f["company_q1_2025_new"]), ((2025, 2), f["company_q2_2025_new"]),
           ((2026, 1), f["company_q1_2026_new"]), ((2026, 2), f["company_q2_2026_new"]),
           ((2026, 3), f["company_q3_2026"])]
plaq = [((2025, 1), f["plaq_q1_2025_new"]), ((2025, 2), f["plaq_q2_2025_new"]),
        ((2026, 1), f["plaq_q1_2026_new"]), ((2026, 2), f["plaq_q2_2026_new"]), ((2026, 3), p3)]
L.append("quarter  spot fee  prior-quarter spot  VG company  Plaquemines")
pq = dict(plaq)
for k, v in company:
    L.append(f"{k[0]} Q{k[1]}   {qspot(*k):6.2f}   {qspot(*prev(*k)):6.2f}             {v:5.2f}       {pq[k]:5.2f}")
for k, v in ((2025, 3), f["company_q3_2025_old"]), ((2025, 4), f["company_q4_2025_old"]):
    L.append(f"{k[0]} Q{k[1]}   {qspot(*k):6.2f}   {qspot(*prev(*k)):6.2f}             {v:5.2f} (older 8-K basis, reference only)")
for name, rows in (("company", company), ("Plaquemines", plaq)):
    (rs, bs_), (rp, bp), gs, gp = stats(rows)
    L.append(f"{name}, 5 quarters: same-quarter spot corr {rs:.2f} slope {bs_:.2f}, avg gap {gs:.2f}; prior-quarter spot corr {rp:.2f} slope {bp:.2f}, avg gap {gp:.2f}")
s3, s2 = qspot(2026, 3), qspot(2026, 2)
L.append(f"Q2 -> Q3 2026: spot fee {s2:.2f} -> {s3:.2f} (+{s3 - s2:.2f}); company {f['company_q2_2026_new']:.2f} -> {f['company_q3_2026']:.2f} (+{f['company_q3_2026'] - f['company_q2_2026_new']:.2f}); Plaquemines {f['plaq_q2_2026_new']:.2f} -> {p3:.2f} (+{p3 - f['plaq_q2_2026_new']:.2f})")
L.append(f"Q3 2026: Plaquemines {p3:.2f} vs same-quarter spot {s3:.2f} and prior-quarter spot {s2:.2f}")

# what the guidance arithmetic implies for Q4 2026 (rough: 3.7 TBtu a cargo, VG's own assumption)
c_high = f["cargo_high_aug11"]; c_mid = (f["cargo_2026_low_aug"] + c_high) / 2
contracted = f["share_2026_contracted_aug11"] * c_high
fy_fee = (contracted * f["company_contracted_fee_2026_aug"] + (c_mid - contracted) * (f["unsold_assumption_aug_low"] + f["unsold_assumption_aug_high"]) / 2) / c_mid
nine = f["company_q1_2026_new"] * f["company_q1_2026_tbtu"] + f["company_q2_2026_new"] * f["company_q2_2026_tbtu"] + f["company_q3_2026"] * f["company_q3_2026_tbtu"]
nine_tbtu = f["company_q1_2026_tbtu"] + f["company_q2_2026_tbtu"] + f["company_q3_2026_tbtu"]
q4_tbtu = (f["cargo_q4_2026_low"] + f["cargo_q4_2026_high"]) / 2 * 3.7
q4_fee = (fy_fee * (nine_tbtu + q4_tbtu) - nine) / q4_tbtu
L.append(f"rough Q4 2026 company fee implied by August guidance arithmetic: {q4_fee:.2f} (full-year {fy_fee:.2f}; nine months realized {nine / nine_tbtu:.2f})")

# the one window where a sale price can be set against VG's own forward assumption
lo = hi = None
for s1 in (0.835, 0.84, 0.845):
    for s2_ in (0.905, 0.91, 0.915):
        for e1 in (-0.005, 0, 0.005):
            for e2 in (-0.005, 0, 0.005):
                c1 = s1 * f["cargo_high_may12"]; c2 = s2_ * f["cargo_high_aug11"]
                fee = (c2 * (f["company_contracted_fee_2026_aug"] + e2) - c1 * (f["fee_2026_contracted_may12"] + e1)) / (c2 - c1)
                lo = fee if lo is None else min(lo, fee); hi = fee if hi is None else max(hi, fee)
c1 = 0.84 * f["cargo_high_may12"]; c2 = 0.91 * f["cargo_high_aug11"]
mid = (c2 * f["company_contracted_fee_2026_aug"] - c1 * f["fee_2026_contracted_may12"]) / (c2 - c1)
L.append(f"cargos sold 12 May to 11 Aug 2026: about {c2 - c1:.0f}, implied fee {mid:.2f} (rounding range {lo:.2f} to {hi:.2f}) vs VG's own forward assumption 9.50-10.50 (May) and 12.50-13.50 (Aug)")
L.append(f"share of 2026 contracted on 25 Feb 2026, three days before the war: {f['share_2026_contracted_feb25']:.0%}")
L.append(f"2026 contracted company fee {f['company_contracted_fee_2026_aug']:.2f} vs FY2025 realized {f['company_fy2025']:.2f}: {f['company_contracted_fee_2026_aug'] / f['company_fy2025'] - 1:+.0%}")

# --- v5 additions -------------------------------------------------------------
import math
def p_two_sided(r, n):
    """p-value for a Pearson correlation; exact t CDF for n-2 = 3 degrees of freedom."""
    assert n == 5
    t_ = abs(r) * math.sqrt(n - 2) / math.sqrt(1 - r * r)
    cdf = 0.5 + (1 / math.pi) * (t_ / (math.sqrt(3) * (1 + t_ * t_ / 3)) + math.atan(t_ / math.sqrt(3)))
    return 2 * (1 - cdf)
L.append("significance with five quarters (two-sided, t with 3 df):")
for name, rows in (("company", company), ("Plaquemines", plaq)):
    ys = [v for _, v in rows]
    same = [qspot(*k) for k, _ in rows]; pr = [qspot(*prev(*k)) for k, _ in rows]
    def corr(a, b):
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        return num / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    r1, r2 = corr(same, ys), corr(pr, ys)
    z = (math.atanh(r2) - math.atanh(r1)) / math.sqrt(2 / (5 - 3))
    pz = math.erfc(abs(z) / math.sqrt(2))
    L.append(f"  {name}: same-quarter r {r1:.2f} p {p_two_sided(r1, 5):.2f}; prior-quarter r {r2:.2f} p {p_two_sided(r2, 5):.2f}; difference p {pz:.2f} (not significant)")
# who ended up with the Q3 2026 spread (ex post), on this basis
calc_fee_q3 = (f["company_q3_2026"] * f["company_q3_2026_tbtu"] - p3 * f["plaq_q3_2026_tbtu"]) / f["calcasieu_q3_2026_tbtu"]
spot3 = s3
keep_calc_buyers = (spot3 - calc_fee_q3) * f["calcasieu_q3_2026_tbtu"] / 1000
keep_plaq_buyers = (spot3 - p3) * f["plaq_q3_2026_tbtu"] / 1000
vg_above_contract = (p3 - calc_fee_q3) * f["plaq_q3_2026_tbtu"] / 1000
total = (spot3 - calc_fee_q3) * f["company_q3_2026_tbtu"] / 1000
L.append(f"Q3 2026 spread above Calcasieu's {calc_fee_q3:.2f} on {f['company_q3_2026_tbtu']:.1f} TBtu at a {spot3:.2f} spot fee: {total:.2f} bn")
L.append(f"  Calcasieu's contract buyers: {keep_calc_buyers:.2f} bn; buyers of Plaquemines' forward-sold cargoes: {keep_plaq_buyers:.2f} bn; Venture Global (Plaquemines above {calc_fee_q3:.2f}): {vg_above_contract:.2f} bn")
L.append(f"  shares: contract buyers {keep_calc_buyers / total:.0%}, forward buyers {keep_plaq_buyers / total:.0%}, VG {vg_above_contract / total:.0%}")

out = "\n".join(L); print(out)
open(os.path.join(RESULTS, "war_capture.txt" if BASIS == "jkm" else "war_capture_ttf.txt"), "w").write(out + "\n")
