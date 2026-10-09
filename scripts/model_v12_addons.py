"""v12 consistency and strengthening (valuation unchanged from model_v10.py):
1. Share count: value per share uses 2.643bn diluted shares (Q2 2026 10-Q Note 16: basic 2,489m + 154m
   dilutive stock options, treasury method). Market value for free-cash-flow yields now uses the same
   count ($34.5bn), not the 2.498bn Class A+B outstanding. Sensitivity: no option dilution.
2. Headline: the price-needs fee against my $3.50 (replacement cost plus a merchant premium).
3. TTF-basis bias: 2011-14 shortage fees are on TTF because free JKM spot data starts in 2017; Asian
   prices ran above European ones after Fukushima, so the shortage average is understated. Sensitivity:
   required shortage share per $1 the 2011-14 fee is understated.
4. Pair payoff by scenario: per $1 of VG short, 24 months, with Cheniere earning its CAPM return
   (beta 0.31 since IPO) adjusted for its own small long-run-fee exposure; borrow cost included.
"""
import os, io, csv, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import valuation as V
    import model_v8 as M8
    import model_v10 as M
from common import RESULTS, read, HH_MULT, SHIP_REGAS

L = []
PX = M.PX; SH = V.SHARES
mk = {r["item"]: float(r["value"]) for r in read("market_inputs_2026-10-08.csv")}
basic_out = (V.bs["class_a_shares"] + V.bs["class_b_shares"]) / 1000
mv_dil = PX * SH; mv_basic = PX * basic_out
v0 = M.value(3.5); v28 = M.value(3.5, roll=True); need = M.needed()
L.append(f"shares: diluted {SH:.3f}bn (basic 2.489 + 154m options), outstanding A+B {basic_out:.3f}bn; market value diluted {mv_dil:.1f}bn, basic {mv_basic:.1f}bn")
L.append(f"  no-option-dilution sensitivity: today {v0 * SH / basic_out:.2f} (vs {v0:.2f}), end-2028 {v28 * SH / basic_out:.2f} (vs {v28:.2f})")
p = M.eps_path(); fcf = {y: p[y]["fcf"] + M8.DIV for y in M.YEARS}
L.append("FCF to common before dividends, yield on diluted market value: " + ", ".join(f"{y} {fcf[y]:.2f} ({fcf[y] / mv_dil:+.1%})" for y in M.YEARS))
L.append(f"  cumulative 2027-31 {sum(fcf.values()):.2f}bn = {sum(fcf.values()) / mv_dil:.0%} of diluted market value; net income {sum(p[y]['eps'] * SH for y in M.YEARS):.2f}bn")
L.append(f"headline: price needs {need:.2f} vs base 3.50 = {need / 3.5 - 1:+.0%}; vs replacement cost ~3.00 = {need / 3.0 - 1:+.0%}")
# TTF bias
tt = {r["month"]: (float(r["ttf_imf_usd_mmbtu"]), float(r["henry_hub_usd_mmbtu"])) for r in read("fred_ttf_hh_monthly.csv")}
fee = {m: t - HH_MULT * h - SHIP_REGAS for m, (t, h) in tt.items() if 2011 <= int(m[:4]) <= 2026}
sy = {2011, 2012, 2013, 2014, 2021, 2022, 2026}
S_ = [v for m, v in fee.items() if int(m[:4]) in sy]; W_ = [v for m, v in fee.items() if 2015 <= int(m[:4]) <= 2020]
n1114 = sum(1 for m in fee if 2011 <= int(m[:4]) <= 2014)
s, w = sum(S_) / len(S_), sum(W_) / len(W_)
L.append("TTF-basis bias: required shortage share by understatement of the 2011-14 fee:")
for d in (0, 1, 2, 3, 5):
    s2 = s + d * n1114 / len(S_); L.append(f"  +${d}: shortage average {s2:.2f}, share needed {(need - w) / (s2 - w):.0%}")
# pair payoff
rf, erp = mk["us10y_2026-10-07"] / 100, mk["damodaran_implied_erp_2026-10-01"] / 100
lng_beta = 0.31; lng_er = rf + lng_beta * erp; lng24 = (1 + lng_er) ** 2 - 1
ch_per = 5.32; lng_px = 272.20; hedge = 1.51; borrow = 0.0041 * 2
gap = 3.078
cases = [("Bear ($2.50)", 2.50, 0.0, 0.25), ("Base ($3.50)", 3.50, 0.0, 0.45), ("Bull ($4.50)", 4.50, 0.0, 0.20), ("Management framework", 3.50, gap, 0.10)]
L.append(f"pair per $1 VG short, 24 months; Cheniere CAPM {lng_er:.1%}/yr ({lng24:.1%} over 24 months) plus {ch_per}/sh per $1 of long-run fee; borrow {borrow:.1%}")
ev = 0.0; rows = []
for lab, l, up, wgt in cases:
    vg_tr = (M.value(l, roll=True, uplift=up) + 0.32) / PX - 1
    lng_tr = lng24 + (l - 3.5) * ch_per / lng_px
    pair = -vg_tr + hedge * lng_tr - borrow
    ev += wgt * pair; rows.append((lab, wgt, vg_tr, lng_tr, pair))
    L.append(f"  {lab:<22} {wgt:.0%}: VG {vg_tr:+.0%}, LNG {lng_tr:+.1%}, pair {pair:+.0%}")
be = hedge * lng24 - borrow
L.append(f"  weighted pair return {ev:+.0%}; break-even: VG's 24-month total return of {be:+.0%} (VG near ${PX * (1 + be) - 0.32:.2f}); of the base-case pair return, {hedge * lng24:+.0%} is simply 1.51x Cheniere's expected return")
out = "\n".join(L); print(out); open(os.path.join(RESULTS, "model_v12_addons.txt"), "w").write(out + "\n")
with open(os.path.join(RESULTS, "pair_payoff_v12.csv"), "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["scenario", "weight", "vg_24m_tr", "lng_24m_tr", "pair_per_usd_short"]); [wr.writerow([a, b, f"{c:.3f}", f"{d:.3f}", f"{e:.3f}"]) for a, b, c, d, e in rows]
