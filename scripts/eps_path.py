"""EPS, free cash flow and net debt, 2026 to 2031, on the base case (futures to 2029,
then Venture Global's own 5.19 median) and on the futures all the way.
Same inputs as valuation.py. D&A path and 2026 interest are ASSUMPTIONS.
"""
LEGACY_NOTE = "LEGACY cross-check from an earlier version (v4-v6). The v7 numbers used in the piece are in results/model_v7.txt, waterfall.txt and pair_v7.txt.\n"
import os
from common import annual_curve, fee_jkm, RESULTS, PRICE_KEY
from valuation import (vol, open_tbtu, COST, CONTRACT_FEE, CAPEX, DEBT_COST, TAX, PREF,
                       NCI, SHARES, ND0, YEARS, bs, g_mid)

DA = {2026: 1.05, 2027: 1.25, 2028: 1.6, 2029: 2.0, 2030: 2.4, 2031: 2.6}   # ASSUMPTION, $bn
INTEREST_2026 = 1.87          # ASSUMPTION: H1 2026 net interest 0.933bn x 2
curve = annual_curve()

def path(fee):
    rows = []
    # 2026 on guidance
    e26 = g_mid / 1000
    pre = e26 - DA[2026] - INTEREST_2026
    eps = (pre * (1 - TAX) - PREF - NCI) / SHARES
    rows.append((2026, e26, eps, None, ND0))
    nd = ND0
    for i, y in enumerate(YEARS):
        ebitda = ((vol[y] - open_tbtu[y]) * CONTRACT_FEE[y] + open_tbtu[y] * fee[y] - COST * vol[y]) / 1000
        interest = nd * DEBT_COST
        pre = ebitda - DA[y] - interest
        eps = (pre * (1 - TAX) - PREF - NCI) / SHARES
        taxable = max(0.0, ebitda - interest - (1.0 + 0.3 * i))
        fcf = ebitda - interest - TAX * taxable - CAPEX[y] - PREF - NCI
        nd -= fcf
        rows.append((y, ebitda, eps, fcf, nd))
    return rows

jk = {y: fee_jkm(curve[y]) for y in YEARS}
base = {**jk, 2030: 5.19, 2031: 5.19}
L = []
for name, fee in (("base: futures to 2029, then 5.19", base), ("futures all the way", jk)):
    L.append(name)
    L.append("year  open fee  EBITDA $bn  EPS $   FCF to equity $bn  net debt $bn")
    for (y, e, eps, fcf, nd) in path(fee):
        of = "guide" if y == 2026 else f"{fee[y]:.2f}"
        L.append(f"{y}  {of:>8}  {e:9.2f}  {eps:6.2f}  {'' if fcf is None else f'{fcf:16.2f}':>16}  {nd:11.1f}")
price = bs[PRICE_KEY]
b = path(base)
L.append(f"P/E at {price}: 2027 {price / b[1][2]:.1f}x, 2028 {price / b[2][2]:.1f}x, 2029 {price / b[3][2]:.1f}x, 2031 {price / b[5][2]:.1f}x (base)")
out = LEGACY_NOTE + "\n".join(L); print(out)
open(os.path.join(RESULTS, "eps_path.txt"), "w").write(out + "\n")
