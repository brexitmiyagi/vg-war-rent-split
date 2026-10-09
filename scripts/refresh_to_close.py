"""Publication-day refresh: the fee the price needs and the scenario returns at a new close.
Usage: python refresh_to_close.py 13.29 [cme_settlements_YYYY-MM-DD.csv]
The CME file defaults to the one in common.CURVE_FILE; pass a newer one once CME publishes it.
"""
import sys, io, contextlib
import common
if len(sys.argv) > 2:
    common.CURVE_FILE = sys.argv[2]
with contextlib.redirect_stdout(io.StringIO()):
    import model_v10 as M
px = float(sys.argv[1]) if len(sys.argv) > 1 else M.PX
lo, hi = -5.0, 30.0
for _ in range(80):
    m = (lo + hi) / 2; lo, hi = (m, hi) if M.value(m) < px else (lo, m)
cases = [("bear", 2.50, 0.0, 0.25), ("base", 3.50, 0.0, 0.45), ("bull", 4.50, 0.0, 0.20), ("management", 3.50, 3.078, 0.10)]
ends = {c: M.value(l, roll=True, uplift=u) for c, l, u, w in cases}
w = sum(ends[c] * x for c, l, u, x in cases)
print(f"close {px:.2f} (CME file {common.CURVE_FILE}): fee needed from 2032 {m:.2f}; base end-2028 {ends['base']:.2f} -> TR {(ends['base'] + 0.32) / px - 1:+.0%}; weighted {w:.2f} -> TR {(w + 0.32) / px - 1:+.0%}")
