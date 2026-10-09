"""The pair: short Venture Global, long Cheniere, dollar-neutral, 24 months.

Both are US Gulf Coast LNG exporters paid in fees over Henry Hub, so the pair takes out most of the
US LNG sector's moves and the general market. What is left is the difference the thesis is about:
how much of each company's value depends on the uncontracted spread in the 2030s.
Scored on total return (dividends included) from the close before publication.
"""
LEGACY_NOTE = "LEGACY cross-check from an earlier version (v4-v6). The v7 numbers used in the piece are in results/model_v7.txt, waterfall.txt and pair_v7.txt.\n"
import os, io, contextlib
from common import read, RESULTS
with contextlib.redirect_stdout(io.StringIO()):
    import valuation_v6 as V6
P = {r["item"]: r for r in read("pair_2026-10-07.csv")}
peers = {r["ticker"]: r for r in read("peers_2026-10.csv")}
L = ["item                                   VG          LNG"]
for k in ("close_2026-10-07", "market_cap_bn", "annual_dividend", "dividend_yield_pct", "buyback_yield_pct", "ebitda_per_usd1_fee_2026_musd", "unsold_2026", "consensus_price_target", "next_earnings"):
    L.append(f"{k:<38} {P[k]['VG']:<11} {P[k]['LNG']}")
vg_ev = float(P["market_cap_bn"]["VG"]) + (float(peers["VG"]["enterprise_value_bn"]) - float(peers["VG"]["market_cap_bn"]))
lng_ev = float(peers["LNG"]["enterprise_value_bn"])
L.append(f"EV / 2026 EBITDA guide midpoint: VG {vg_ev / float(peers['VG']['ebitda_2026_guide_mid_bn']):.1f}x (EV {vg_ev:.1f}bn at Oct 7), LNG {lng_ev / float(peers['LNG']['ebitda_2026_guide_mid_bn']):.1f}x")
for t in ("VG", "LNG"):
    s = float(P["ebitda_per_usd1_fee_2026_musd"][t]) / 1000 / float(P["market_cap_bn"][t])
    L.append(f"2026 EBITDA per $1 of fee as % of market cap: {t} {s:.2%}")
L.append(f"VG long-run: each $1 of open fee from 2029 is worth {V6.slope:.2f} a share, {V6.slope / V6.px:.0%} of the price (valuation_v6.py)")
L.append("Cheniere plans on a $2.50-3.00 long-run margin and has less than 1 Mt of 2026 unsold (Q2 2026 call); no comparable long-run sensitivity is published")
out = LEGACY_NOTE + "\n".join(L); print(out)
open(os.path.join(RESULTS, "pair.txt"), "w").write(out + "\n")
