"""v11 additions on top of model_v10.py (valuation unchanged):
1. Through-cycle test: how often the market must be in shortage after 2032 for the long-run fee to reach
   the $4.49 the price needs, using the fee by regime (TTF basis, 2011-Sep 2026).
2. Free cash flow to common (before common dividends) 2027-31 against market value.
3. Quarterly estimates Q3 2026E-Q4 2027E (sell-side convention). Q3/Q4 2026 from the Q3 cargo 8-K and
   the 2026 guidance midpoint; 2027 quarters allocate the annual model by the deck's cargo forecast and
   the monthly CME strip, so the four quarters sum to the annual numbers.
"""
import os, io, csv, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import valuation as V
    import model_v8 as M8
    import model_v9 as M9
    import model_v10 as M
from common import RESULTS, read, HH_MULT, SHIP_REGAS, CURVE_FILE

L = []
SH = V.SHARES; TAX = V.TAX; PX = M.PX
SHARES_OUT = (V.bs["class_a_shares"] + V.bs["class_b_shares"]) / 1000

# 1. through-cycle test
tt = {r["month"]: (float(r["ttf_imf_usd_mmbtu"]), float(r["henry_hub_usd_mmbtu"])) for r in read("fred_ttf_hh_monthly.csv")}
fee = {m: t - HH_MULT * h - SHIP_REGAS for m, (t, h) in tt.items() if 2011 <= int(m[:4]) <= 2026}
short_y = {2011, 2012, 2013, 2014, 2021, 2022, 2026}
wave_y = set(range(2015, 2021)); reb_y = {2023, 2024, 2025}
S_ = [v for m, v in fee.items() if int(m[:4]) in short_y]
W_ = [v for m, v in fee.items() if int(m[:4]) in wave_y]
R_ = [v for m, v in fee.items() if int(m[:4]) in reb_y]
avg = lambda x: sum(x) / len(x)
s, w, r = avg(S_), avg(W_), avg(R_); nonshort = avg(W_ + R_)
share_hist = len(S_) / len(fee)
need = M.needed()
p_w = (need - w) / (s - w); p_nr = (need - nonshort) / (s - nonshort)
p_base_w = (3.50 - w) / (s - w)
L.append(f"through-cycle (TTF basis, 2011-Sep 2026, {len(fee)} months): shortage months {len(S_)} ({share_hist:.0%}) avg {s:.2f}; wave avg {w:.2f}; rebalancing avg {r:.2f}; all non-shortage {nonshort:.2f}; all-months avg {avg(list(fee.values())):.2f}")
L.append(f"  price needs {need:.2f}: shortage share needed {p_w:.0%} if other years look like 2015-20, {p_nr:.0%} if they look like 2015-25 together; my 3.50 implies {p_base_w:.0%} (wave-like other years)")
q3_capture = 6.79 / 17.43
L.append(f"  capture in this shortage: Q3 2026 company fee 6.79 vs spot-equivalent 17.43 = {q3_capture:.0%}")

# 2. FCF to common before common dividends
p = M.eps_path()
mcap = PX * SHARES_OUT
fcfs = {y: p[y]["fcf"] + M8.DIV for y in M.YEARS}
L.append(f"market value of equity {mcap:.1f}bn ({SHARES_OUT:.3f}bn Class A+B at {PX}); net income vs FCF to common before dividends:")
for y in M.YEARS:
    ni = p[y]["eps"] * SH
    L.append(f"  {y}: net income {ni:5.2f}  FCF {fcfs[y]:5.2f}  FCF yield {fcfs[y] / mcap:+.1%}")
L.append(f"  2027-31 cumulative FCF {sum(fcfs.values()):.2f}bn vs net income {sum(p[y]['eps'] * SH for y in M.YEARS):.2f}bn")

# 3. quarterly estimates
q3_ebitda = 465.8 * (6.79 - M8.C26) / 1000
h2 = (V.bs["ebitda_guide_2026_low"] + V.bs["ebitda_guide_2026_high"]) / 2000 - V.bs["h1_2026_adjusted_ebitda"] / 1000
q4_ebitda = h2 - q3_ebitda
da_h2 = (M.DA10[2026] - 0.511) / 2
def q_eps(e, da, intr):
    ebt = e - da - intr
    return (ebt * (1 - TAX) - (V.PREF + V.NCI) / 4) / SH
Q = [("Q3 2026E", 465.8, q3_ebitda, da_h2, 0.489, q_eps(q3_ebitda, da_h2, 0.489)),
     ("Q4 2026E", None, q4_ebitda, da_h2, 0.489, q_eps(q4_ebitda, da_h2, 0.489))]
# 2027 quarters
rows, _ = M.series(3.5)
r27 = rows[2027]
vol_q = [129.5 * 3.7, 126.0 * 3.7]
rest = r27["vol"] - sum(vol_q); cp2_q = [0.0, 0.0, 192.0 / 3, 192.0 * 2 / 3]
non = [vol_q[0], vol_q[1], (rest - 192.0) / 2, (rest - 192.0) / 2]
vols = [non[i] + cp2_q[i] for i in range(4)]
open_non = r27["open"] - 192.0
op_q = [open_non * non[i] / sum(non) + cp2_q[i] for i in range(4)]
cme = read(CURVE_FILE)
mf = {}
for rr in cme:
    mon, yy = rr["month"].split()
    if yy == "27":
        mf[mon] = float(rr["jkm_usd_mmbtu"]) - HH_MULT * float(rr["henry_hub_usd_mmbtu"]) - SHIP_REGAS
qm = [["JAN", "FEB", "MAR"], ["APR", "MAY", "JUN"], ["JUL", "AUG", "SEP"], ["OCT", "NOV", "DEC"]]
qfee = [sum(mf[m] for m in g) / 3 for g in qm]
open_margin_raw = [op_q[i] * qfee[i] for i in range(4)]
open_rev = r27["open"] * M.FUT[2027] / 1000
open_q = [open_rev * x / sum(open_margin_raw) for x in open_margin_raw]
con_rev = r27["ebitda"] - r27["eo"] - r27["ec"] + r27["ec"]  # placeholder, recomputed below
cost_total = (M.C_EX * r27["vol"]) / 1000 + M8.BASIS[2027]
con_rev = r27["ebitda"] + cost_total - open_rev
con_q = [con_rev * (vols[i] - op_q[i]) / (r27["vol"] - r27["open"]) for i in range(4)]
cost_q = [M.C_EX * vols[i] / 1000 + M8.BASIS[2027] / 4 for i in range(4)]
e_q = [con_q[i] + open_q[i] - cost_q[i] for i in range(4)]
cp2_da = M9.DA_RATE * 0.55 * M.CP2_COST * 0.25
da_q = [(M.DA10[2027] - cp2_da) / 4] * 3 + [(M.DA10[2027] - cp2_da) / 4 + cp2_da]
int_q = [p[2027]["pl_int"] / 4] * 4
for i in range(4):
    Q.append((f"Q{i + 1} 2027E", vols[i], e_q[i], da_q[i], int_q[i], q_eps(e_q[i], da_q[i], int_q[i])))
L.append("quarterly estimates: quarter, volume TBtu, open TBtu, strip fee, EBITDA, D&A, interest, EPS")
for k, (lab, v, e, da, it, eps) in enumerate(Q):
    extra = "" if k < 2 else f"  open {op_q[k - 2]:5.0f}  strip {qfee[k - 2]:5.2f}"
    L.append(f"  {lab}  {'' if v is None else f'{v:6.1f}'}{extra}  EBITDA {e:5.2f}  D&A {da:4.2f}  int {it:4.2f}  EPS {eps:5.2f}")
L.append(f"  check: 2027 quarters sum EBITDA {sum(e_q):.2f} (annual {r27['ebitda']:.2f}), EPS {sum(x[5] for x in Q[2:]):.2f} (annual {p[2027]['eps']:.2f}); 2026 H2 EBITDA {q3_ebitda + q4_ebitda:.2f} (guide-implied {h2:.2f})")
L.append(f"  Q3 2026E uses the 8-K fee 6.79 on 465.8 TBtu and the 2026-calibrated all-in cost {M8.C26:.3f}; Q4 2026E is the guidance-midpoint remainder")
out = "\n".join(L); print(out)
open(os.path.join(RESULTS, "model_v11_addons.txt"), "w").write(out + "\n")
with open(os.path.join(RESULTS, "quarterly_v11.csv"), "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["quarter", "volume_tbtu", "ebitda_bn", "da_bn", "interest_bn", "eps"])
    for lab, v, e, da, it, eps in Q: wr.writerow([lab, "" if v is None else f"{v:.1f}", f"{e:.2f}", f"{da:.2f}", f"{it:.2f}", f"{eps:.2f}"])
with open(os.path.join(RESULTS, "fcf_v11.csv"), "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["year", "net_income_bn", "fcf_to_common_before_div_bn", "fcf_yield"])
    for y in M.YEARS: wr.writerow([y, f"{p[y]['eps'] * SH:.2f}", f"{fcfs[y]:.2f}", f"{fcfs[y] / mcap:.3f}"])
