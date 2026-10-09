"""v13: rating dependence and honest trade edge (valuation unchanged from model_v10.py).
1. Scenario values and weighted value at the base rates (7%/10%) and at CAPM-consistent rates (6%/9%).
2. Pair edge decomposition: VG-specific part vs 1.51x Cheniere's expected return vs borrow; 2-year volatility.
3. Put spread: expected payoff on my scenario weights vs live mid and executable prices (8 Oct, ~10:40 ET).
4. Intraday: fee the price needs at VG's 8 Oct intraday price (not a close).
"""
import os, io, contextlib, math
with contextlib.redirect_stdout(io.StringIO()):
    import model_v10 as M
from common import RESULTS, read
mk = {r["item"]: r["value"] for r in read("market_inputs_2026-10-08.csv")}
PX = M.PX; gap = 3.078; L = []
cases = [("bear", 2.50, 0.0, 0.25), ("base", 3.50, 0.0, 0.45), ("bull", 4.50, 0.0, 0.20), ("management", 3.50, gap, 0.10)]
for lab, rc, ro in (("base rates 7%/10%", 0.07, 0.10), ("CAPM-consistent 6%/9%", 0.06, 0.09)):
    v = [(c, M.value(l, rc=rc, ro=ro, uplift=u), M.value(l, roll=True, rc=rc, ro=ro, uplift=u), w) for c, l, u, w in cases]
    ev0 = sum(x[1] * x[3] for x in v); ev28 = sum(x[2] * x[3] for x in v)
    L.append(f"{lab}: today " + ", ".join(f"{c} {a:.2f}" for c, a, b, w in v) + f" | end-2028 " + ", ".join(f"{c} {b:.2f}" for c, a, b, w in v)
             + f" | weighted today {ev0:.2f}, end-2028 {ev28:.2f}, 24m TR {(ev28 + 0.32) / PX - 1:+.0%}")
# pair decomposition (from model_v12_addons inputs)
vg_tr = {c: (M.value(l, roll=True, uplift=u) + 0.32) / PX - 1 for c, l, u, w in cases}
wts = {c: w for c, l, u, w in cases}
lng24 = (1 + 0.0528 + 0.31 * 0.042) ** 2 - 1
lng_tr = {c: lng24 + (l - 3.5) * 5.32 / 272.2 for c, l, u, w in cases}
vg_part = -sum(wts[c] * vg_tr[c] for c in wts); lng_part = 1.51 * sum(wts[c] * lng_tr[c] for c in wts); borrow = 0.0082
vol2 = 0.60 * math.sqrt(2)
L.append(f"pair weighted {vg_part + lng_part - borrow:+.1%} = VG-specific {vg_part:+.1%} + 1.51x Cheniere expected {lng_part:+.1%} - borrow {borrow:.1%}; 2-year volatility ~{vol2:.0%}; VG-specific edge / 2-yr vol = {vg_part / vol2:.2f}")
# put spread
ends = {c: M.value(l, roll=True, uplift=u) for c, l, u, w in cases}
pay = {c: min(2.5, max(0.0, 12.5 - ends[c])) for c in ends}
ev = sum(wts[c] * pay[c] for c in wts)
for lab, cost in (("last trades (Oct 5/7)", 1.20), ("live mid (12.5: 3.45, 10: 2.25)", 1.20), ("live executable (pay 3.60, sell 2.05)", 1.55)):
    L.append(f"Jan-2029 12.5/10 put spread, {lab}: cost {cost:.2f}; expected payoff on my weights {ev:.2f} -> {ev / cost - 1:+.0%}")
L.append("  payoffs by scenario: " + ", ".join(f"{c} {pay[c]:.2f}" for c in pay) + "; live implied vols ~51-55% vs 78% realized since the war")
# intraday
px_i = float(mk["vg_intraday_2026-10-08_1040ET"])
lo, hi = -5.0, 30.0
for _ in range(80):
    m = (lo + hi) / 2; lo, hi = (m, hi) if M.value(m) < px_i else (lo, m)
L.append(f"intraday 8 Oct ~10:40 ET: VG {px_i} (+{px_i / PX - 1:.1%} vs 7 Oct close); fee the price needs {m:.2f} (vs {M.needed():.2f})")
out = "\n".join(L); print(out); open(os.path.join(RESULTS, "model_v13_addons.txt"), "w").write(out + "\n")
