"""Credit cross-check: the single yield that prices VG's fixed-rate notes at the fair value in its 10-Q,
against the 10-year Treasury, and the new-issue spreads of 2026. Series, coupons and maturities from the
FY2025 10-K and Q2 2026 10-Q (data/vg_fixed_rate_notes.csv; a few days/months are assumed, flagged there)."""
import os, csv, datetime as dt
from common import read, RESULTS
N = read("vg_fixed_rate_notes.csv"); mk = {r["item"]: float(r["value"]) for r in read("market_inputs_2026-10-08.csv")}
def pv(y, asof, notes):
    tot = 0.0
    for n in notes:
        P = float(n["principal_usd_m"]); c = float(n["coupon_pct"]) / 100; t = (dt.date.fromisoformat(n["maturity"]) - asof).days / 365.25; k = 0
        while t - 0.5 * k > 0:
            tt = t - 0.5 * k; tot += (P * c / 2 + (P if k == 0 else 0)) / (1 + y / 2) ** (2 * tt); k += 1
    return tot
L = []
for asof, fv, excl, tsy in ((dt.date(2025, 12, 31), 25510, ("VGLNG2034", "VGLNG2036", "VGCP2036"), mk["us10y_2025-12-31"]),
                            (dt.date(2026, 6, 30), 23911, ("VGLNG2028",), mk["us10y_2026-06-30"])):
    notes = [n for n in N if n["issuer"] + n["series"] not in excl]
    face = sum(float(n["principal_usd_m"]) for n in notes); lo, hi = 0.0, 0.3
    for _ in range(80):
        m = (lo + hi) / 2; lo, hi = (m, hi) if pv(m, asof, notes) > fv else (lo, m)
    L.append(f"{asof}: face {face:,.0f}, 10-Q fair value {fv:,} ({fv / face:.1%}), implied yield {m:.2%}, 10-year {tsy:.2f}%, spread {m * 100 - tsy:.2f} pts")
s34 = mk["vglng_2034_coupon"] - mk["us10y_2026-06-02"]; s36 = mk["vglng_2036_coupon"] - mk["us10y_2026-06-02"]; scp = mk["vgcp_2036_coupon"] - mk["us10y_2026-04-15"]
now = mk["us10y_2026-10-07"]
L.append(f"new-issue spreads over the 10-year: VGLNG 2034 {s34:.2f}, VGLNG 2036 {s36:.2f} (June 2026, at par); VGCP 2036 {scp:.2f} (April 2026)")
L.append(f"at today's 10-year {now:.2f}%: parent secured ~{now + (s34 + s36) / 2:.2f}%, Calcasieu project secured ~{now + scp:.2f}%")
L.append("caveat: the June fair value implies a much wider spread than the par pricing of the June notes; the two can't both be clean reads, so the piece leans on new-issue spreads.")
out = "\n".join(L); print(out); open(os.path.join(RESULTS, "bond_check_v10.txt"), "w").write(out + "\n")
