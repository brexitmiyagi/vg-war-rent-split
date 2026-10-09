"""Venture Global against the two other listed US LNG developers. Market data is S&P Global
via stockanalysis.com on the date in the file; EBITDA 2026 is each company's own guidance midpoint."""
import os
from common import read, RESULTS
L = ["company  EV $bn  EV/EBITDA ttm  EV/2026 guide  debt/EBITDA  note"]
for r in read("peers_2026-10.csv"):
    ev = float(r["enterprise_value_bn"])
    g = r["ebitda_2026_guide_mid_bn"]
    fwd = f"{ev / float(g):.1f}x" if g else "n/m"
    ttm = f"{float(r['ev_ebitda_ttm']):.1f}x" if r["ev_ebitda_ttm"] else "n/m"
    de = f"{float(r['debt_to_ebitda_ttm']):.1f}x" if r["debt_to_ebitda_ttm"] else "n/m"
    L.append(f"{r['ticker']:<6} {ev:6.1f}  {ttm:>6}  {fwd:>6}  {de:>5}  {r['contracted_note']}")
out = "\n".join(L); print(out)
open(os.path.join(RESULTS, "peers.txt"), "w").write(out + "\n")
