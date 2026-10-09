"""My estimates against the Street. Consensus: S&P Global via stockanalysis.com
(EPS 2026 1.69, 2027 1.00, checked 25 Sep 2026 page, read 7 Oct 2026). S&P's 2028 figure is
behind a paywall, so I leave it blank rather than guess. Mine come from eps_path.py."""
LEGACY_NOTE = "LEGACY cross-check from an earlier version (v4-v6). The v7 numbers used in the piece are in results/model_v7.txt, waterfall.txt and pair_v7.txt.\n"
import os
from common import RESULTS, annual_curve, fee_jkm
from eps_path import path, base, jk
CONS = {2026: 1.69, 2027: 1.00}
L = ["year  my EBITDA $bn (base)  my EPS base  my EPS futures-all-the-way  consensus EPS"]
b, f = path(base), path(jk)
for (y, e, eps, _, _), (_, _, eps_f, _, _) in zip(b, f):
    if y > 2028: break
    c = CONS.get(y)
    L.append(f"{y}  {e:8.2f}  {eps:8.2f}  {eps_f:8.2f}  {'n/a' if c is None else f'{c:.2f}'}")
out = LEGACY_NOTE + "\n".join(L); print(out)
open(os.path.join(RESULTS, "estimates_vs_consensus.txt"), "w").write(out + "\n")
