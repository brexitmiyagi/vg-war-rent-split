"""v15: evidence that does not depend on my own assumptions (valuation core unchanged from model_v10.py).
1. Contract-fee database: every publicly reported fee on new US LNG contracts, 2023-26, against the $4.49 the price needs.
2. Market- and deal-implied returns: Sempra's Port Arthur FID numbers, Cheniere/CQP EBITDA yields.
3. Options-implied (risk-neutral) distribution for Jan-2029 vs my four scenario weights.
4. Peer multiples incl. Cheniere Partners (TTM) next to the 2026-guidance multiples from v14.
5. Merchant exposure: VG's contract portfolio and the bolt-on contracting policy.
6. Corrections: parent-note coupon (2029-32 series) and beta statistics (daily vs weekly, R^2).
"""
import os, io, csv, math, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import model_v10 as M
from common import RESULTS, read
L = []
# 1. contract fees
db = read("contract_fee_database_v15.csv")
L.append("1. Reported fees on new US LNG contracts (115%-of-HH basis, midpoint) vs $4.49 needed:")
mx = 0
for r in db:
    v = float(r["fee_on_115pct_basis_mid"]); mx = max(mx, v)
    L.append(f"   {r['date_reported']}  {r['seller_or_market']:<45} {r['tenor_years']:>2}y  {v:.2f}")
L.append(f"   highest reported: {mx:.2f}; gap to 4.49: {4.49 - mx:.2f}; none at or above 4.49")
# 2. Port Arthur project return at FID (Sempra figures)
capex, ebitda = 13.0, 0.41 / 0.25
sched = {2023: 0.15, 2024: 0.30, 2025: 0.30, 2026: 0.20, 2027: 0.05}
def irr(cfs):
    lo, hi = -0.5, 0.5
    for _ in range(200):
        m = (lo + hi) / 2
        npv = sum(c / (1 + m) ** t for t, c in enumerate(cfs))
        lo, hi = (m, hi) if npv > 0 else (lo, m)
    return m
def pa_cfs(years):
    cfs = []
    for y in range(2023, 2028 + years):
        c = -capex * sched.get(y, 0.0)
        if y == 2027: c += ebitda * 0.5
        if 2028 <= y < 2028 + years: c += ebitda
        cfs.append(c)
    return cfs
MACRS15 = [0.05, 0.095, 0.0855, 0.077, 0.0693, 0.0623, 0.059, 0.059, 0.0591, 0.059, 0.0591, 0.059, 0.0591, 0.059, 0.0591, 0.0295]
def pa_cfs_at(years):
    cfs = []
    for y in range(2023, 2028 + years):
        eb = ebitda * 0.5 if y == 2027 else (ebitda if 2028 <= y < 2028 + years else 0.0)
        dep = capex * MACRS15[y - 2027] if 0 <= y - 2027 < len(MACRS15) else 0.0
        cfs.append(-capex * sched.get(y, 0.0) + eb - 0.21 * max(0.0, eb - dep))
    return cfs
e_yield = ebitda / capex
L.append(f"2. Port Arthur Phase 1 (Sempra FID numbers): project EBITDA ~{ebitda:.2f}bn/yr on {capex:.0f}bn capex = {e_yield:.1%} EBITDA yield; "
         f"unlevered pre-tax IRR {irr(pa_cfs(20)):.1%} over 20 years of contracts ({irr(pa_cfs(30)):.1%} over 30); after 21% tax with 15-year MACRS {irr(pa_cfs_at(20)):.1%} ({irr(pa_cfs_at(30)):.1%})")
mk = {r["item"]: r["value"] for r in read("deal_economics_v15.csv")}
lng_ev = 206.534 * 272.20 / 1000 + (1.411 + 22.632 - 1.099 - 0.420) + (484.058 - 239.9) * 63.44 / 1000
cqp_ev = 484.058 * 63.44 / 1000 + float(mk["cqp_debt_2026-06-30"]) - float(mk["cqp_cash_restricted_2026-06-30"])
vg_ev = 2.643 * 13.05 + (42.386 - 3.120 - 0.068 - 1.402) + 3.0 + 3.507
L.append(f"   Cheniere EV {lng_ev:.1f}bn on its own 'run rate' of $8bn+ at $2.50-3 margins: EBITDA yield ~{8.0 / lng_ev:.1%} (11.8x); "
         f"CQP EV {cqp_ev:.1f}bn on TTM EBITDA 4.56bn: {4.56 / cqp_ev:.1%}")
L.append("   Louisiana LNG: Stonepeak's $5.7bn bought infrastructure equity behind a tolling agreement with cost overruns borne by HoldCo; return terms not disclosed")
# 3. options-implied distribution
rows = [r for r in csv.reader(open(os.path.join(os.path.dirname(__file__), "..", "data", "options_jan2029_chain_2026-10-08.csv"))) if r and not r[0].startswith("#")][1:]
calls = {float(r[1]): (float(r[2]) + float(r[3])) / 2 for r in rows if r[0] == "call"}
puts = {float(r[1]): (float(r[2]) + float(r[3])) / 2 for r in rows if r[0] == "put"}
T = (math.floor((2029 - 2026) * 365) - 262) / 365  # 8 Oct 2026 -> 19 Jan 2029
T = 833 / 365
r_ = 0.045; g = math.exp(r_ * T)
ks = sorted(calls)
cdf = []
for a, b in zip(ks[:-1], ks[1:]):
    p_above = g * (calls[a] - calls[b]) / (b - a)
    cdf.append(((a + b) / 2, 1 - p_above))
pc = []
pk = sorted(puts)
for a, b in zip(pk[:-1], pk[1:]):
    if b - a <= 5: pc.append(((a + b) / 2, g * (puts[b] - puts[a]) / (b - a)))
def interp(x, pts):
    pts = sorted(pts)
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        if x0 <= x <= x1: return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return None
med = None
for (x0, y0), (x1, y1) in zip(cdf[:-1], cdf[1:]):
    if y0 <= 0.5 <= y1: med = x0 + (x1 - x0) * (0.5 - y0) / (y1 - y0)
fwd = 13.205 * g - 0.16 * T
L.append(f"3. Risk-neutral CDF from Jan-2029 call mids (r {r_:.1%}, T {T:.2f}y): " + ", ".join(f"P(<{k:.2f})={p:.0%}" for k, p in cdf))
L.append("   from put mids: " + ", ".join(f"P(<{k:.2f})={p:.0%}" for k, p in pc))
w = [(6.29, 0.25), (11.27, 0.45), (16.24, 0.20), (21.49, 0.10)]
for k in (8.75, 11.25, 13.75, 18.75):
    mine = sum(p for v, p in w if v < k)
    L.append(f"   P(price < {k:.2f} at Jan 2029): options (calls) {interp(k, cdf):.0%} vs my weights {mine:.0%}")
L.append(f"   options-implied median ~{med:.2f}; risk-neutral mean = forward ~{fwd:.2f}; my weighted end-2028 value 12.04; 12.5 put open interest only 22 contracts")
open(os.path.join(RESULTS, "options_implied_v15.csv"), "w").write("strike_mid,cdf_calls\n" + "\n".join(f"{k:.2f},{p:.3f}" for k, p in cdf) + "\n")
# 4. multiples
L.append(f"4. EV/EBITDA: 2026 guidance VG {vg_ev / 8.9:.1f}x, Cheniere {lng_ev / 8.15:.1f}x; TTM (S&P) VG {vg_ev / 7.35:.1f}x, Cheniere {lng_ev / 7.83:.1f}x, CQP {cqp_ev / 4.56:.1f}x")
# 5. merchant exposure
tot, lt, mt, av = 85, 47, 6, 32
L.append(f"5. Contract portfolio (Q2 deck): {lt}/{mt}/{av} of {tot} MTPA long/medium/available -> {av / tot:.0%} uncontracted today, {(av + mt) / tot:.0%} once medium-term rolls off; "
         f"each 1 MTPA left merchant = 52 TBtu; at $1 of fee that is ~$52m a year")
# 6. corrections
notes = [(3000, 9.5), (1500, 7.0), (2250, 8.375), (2000, 9.875)]
cpn = sum(a * c for a, c in notes) / sum(a for a, c in notes)
L.append(f"6. VGLNG notes due 2029-32: {sum(a for a, c in notes) / 1000:.2f}bn at a blended {cpn:.2f}% (the 8.38% figure covers all 11.0bn incl. 2034/36); with Plaquemines bank debt (2029) 2.683bn and CP2 bridge (2028) 1.979bn: {(sum(a for a, c in notes) + 2683 + 1979) / 1000:.1f}bn due 2028-32")
px = list(csv.DictReader(open(os.path.join(os.path.dirname(__file__), "..", "data", "prices_vg_lng_spy_daily.csv"))))
def stats(rows, a, b):
    x = [math.log(float(r2[a]) / float(r1[a])) for r1, r2 in zip(rows[:-1], rows[1:])]
    y = [math.log(float(r2[b]) / float(r1[b])) for r1, r2 in zip(rows[:-1], rows[1:])]
    n = len(x); mx_, my_ = sum(x) / n, sum(y) / n
    sxy = sum((u - mx_) * (v - my_) for u, v in zip(x, y)); syy = sum((v - my_) ** 2 for v in y); sxx = sum((u - mx_) ** 2 for u in x)
    return n, sxy / syy, sxy / math.sqrt(sxx * syy)
n, b, c = stats(px, "vg_adjclose", "spy_adjclose")
import datetime
wk = {}
for r in px:
    d = datetime.date.fromisoformat(r["date"]); wk[d - datetime.timedelta(days=d.weekday())] = r
wrows = [wk[k] for k in sorted(wk)]
n2, b2, c2 = stats(wrows, "vg_adjclose", "spy_adjclose")
L.append(f"   beta VG on SPY since IPO: daily {b:.2f} (corr {c:.2f}, R^2 {c * c:.0%}, n {n}); weekly {b2:.2f} (corr {c2:.2f}, R^2 {c2 * c2:.0%}, n {n2}). The 0.92 used is the daily figure and explains ~3% of VG's moves.")
out = "\n".join(L); print(out); open(os.path.join(RESULTS, "model_v15_addons.txt"), "w").write(out + "\n")
