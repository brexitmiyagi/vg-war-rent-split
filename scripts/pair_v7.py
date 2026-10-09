"""Pair construction from daily prices (Yahoo Finance adjusted closes, data/prices_vg_lng_spy_daily.csv).

Hedge ratio = beta of VG daily returns on LNG daily returns since the war began (27 Feb 2026).
Reports vols, correlation, pair vol dollar-neutral and beta-hedged, and the carry
(borrow fee and dividends) from data/pair_stats_inputs.csv.
"""
import os, math
from common import read, RESULTS
rows = read("prices_vg_lng_spy_daily.csv")
def stats(start):
    r = [x for x in rows if x["date"] >= start]
    p = {k: [float(x[k]) for x in r] for k in ("vg_adjclose", "lng_adjclose", "spy_adjclose")}
    R = {k: [math.log(v[i] / v[i - 1]) for i in range(1, len(v))] for k, v in p.items()}
    n = len(R["vg_adjclose"])
    m = {k: sum(v) / n for k, v in R.items()}
    cov = lambda a, b: sum((R[a][i] - m[a]) * (R[b][i] - m[b]) for i in range(n)) / (n - 1)
    vg, lng = "vg_adjclose", "lng_adjclose"
    vol = lambda a: math.sqrt(cov(a, a) * 252)
    beta = cov(vg, lng) / cov(lng, lng); rho = cov(vg, lng) / math.sqrt(cov(vg, vg) * cov(lng, lng))
    pv_dn = math.sqrt((cov(vg, vg) + cov(lng, lng) - 2 * cov(vg, lng)) * 252)
    pv_b = vol(vg) * math.sqrt(1 - rho * rho)
    return dict(start=start, n=n, vol_vg=vol(vg), vol_lng=vol(lng), rho=rho, beta=beta, pair_vol_dollar_neutral=pv_dn, pair_vol_beta_hedged=pv_b)
L = []
for s in ("2025-01-27", "2025-10-08", "2026-02-27"):
    d = stats(s)
    L.append("from {start}: n={n}, vol VG {vol_vg:.0%}, vol LNG {vol_lng:.0%}, corr {rho:.2f}, beta VG on LNG {beta:.2f}, pair vol dollar-neutral {pair_vol_dollar_neutral:.0%}, beta-hedged {pair_vol_beta_hedged:.0%}".format(**d))
war = stats("2026-02-27")
inp = {r["item"]: r["value"] for r in read("pair_stats_inputs.csv")}
h = war["beta"]
borrow = 0.0041; vg_y = 0.16 / 13.05; lng_y = 2.22 / 272.20
carry = -borrow - vg_y + h * lng_y
L.append(f"sizing: for each $1 short VG, ${h:.2f} long LNG (beta since the war began)")
L.append(f"carry a year per $1 short VG: borrow -{borrow:.2%}, VG dividend paid -{vg_y:.2%}, LNG dividends received +{h * lng_y:.2%} -> {carry:+.2%}")
L.append(f"even beta-hedged the pair runs about {war['pair_vol_beta_hedged']:.0%} annual volatility: most of it is VG's own risk, which is the bet")
out = "\n".join(L); print(out)
open(os.path.join(RESULTS, "pair_v7.txt"), "w").write(out + "\n")
