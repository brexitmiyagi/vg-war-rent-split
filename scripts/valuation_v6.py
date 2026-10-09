"""v6 valuation layer on top of sotp.py.

1. Payoff line: value per share against a flat open-cargo fee from 2029 (CME futures kept for
   2027-28), so the reader picks the fee instead of me picking probabilities.
2. Central case = the market's own price: a flat open fee from 2029 equal to the CME futures
   average for 2029-31 (JKM method, Oct 6 settlements), with CP2's contract fees raised by 0.85
   (point 4) by half of what the lender sizing implies (+0.40): the Q1 2026 deck says VG signs new
   20-year SPAs "while maintaining industry low long-term pricing", which argues against the full
   back-solve. Venture Global sells forward, so the forward is roughly the price it will sign at.
   The 24-month target is this case rolled to the end of 2028.
3. Management's framework: on the Q4 2025 call (2 Mar 2026) Mike Sabel said a $3 fee on
   uncontracted volumes gives 2029 EBITDA of "about $11 billion" and $5 gives $17 billion. My
   model gives much less. I size the gap at $3 and add it as extra EBITDA from 2029 (taxed,
   discounted at the contracted rate) to show what the stock is worth if management is right.
4. Contract fees: CP2's long-term fees aren't disclosed. Back-solving its lenders' 1.40x sizing
   (waterfall.py) points to fixed fees well above Calcasieu's. I show +0.85 on CP2 SPA volume.
5. Henry Hub: on open volume, +$1 of Henry Hub is -$1.15 of fee. Value per share per $1 of HH.
6. Peer-multiple cross-check: 2030/2031 EBITDA at VG's own and Cheniere's 2026 multiples.
"""
LEGACY_NOTE = "LEGACY cross-check from an earlier version (v4-v6). The v7 numbers used in the piece are in results/model_v7.txt, waterfall.txt and pair_v7.txt.\n"
import os, io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import sotp as S
    from eps_path import path
from common import RESULTS, PRICE_KEY

px = S.bs[PRICE_KEY]
jk = S.jk
YEARS = S.YEARS

def value(fee29, uplift=0.0, cp2_extra=0.0, rc=S.RC, ro=S.RO, roll_to_2028=False):
    """Equity per share. fee29: flat open fee from 2029 (futures for 2027-28).
    uplift: extra pre-tax EBITDA $bn a year from 2029 (management-framework gap).
    cp2_extra: extra fee $/MMBtu on contracted volume above Calcasieu + Plaquemines (CP2 SPAs) from 2030."""
    fee = {**jk, 2029: fee29, 2030: fee29, 2031: fee29}
    base_con = 520 + 1040
    pv = 0.0
    yrs = (2029, 2030, 2031) if roll_to_2028 else tuple(YEARS)
    for t, y in enumerate(yrs, start=1):
        con = S.vol[y] - S.open_tbtu[y]
        ec = con * (S.CONTRACT_FEE[y] - S.COST) / 1000
        if y >= 2030:
            ec += max(0.0, con - base_con) * cp2_extra / 1000
        if y >= 2029:
            ec += uplift
        eo = S.open_tbtu[y] * (fee[y] - S.COST) / 1000
        pv += (ec * (1 - S.TAX) + S.TAX * S.DA[y]) / (1 + rc) ** t + eo * (1 - S.TAX) / (1 + ro) ** t - S.CAPEX[y] / (1 + rc) ** t
    n_years = len(yrs)
    con = S.vol[2031] - S.open_tbtu[2031]
    share_c = con / S.vol[2031]
    ec = con * (2.45 - S.COST) / 1000 - 1.0 * share_c + max(0.0, con - base_con) * cp2_extra / 1000 + uplift
    cc = ec * (1 - S.TAX) + S.TAX * 2.6
    n = 2049 - 2031
    pv += cc * (1 - (1 + rc) ** -n) / rc / (1 + rc) ** n_years
    pv += con * (fee29 - S.COST) / 1000 * (1 - S.TAX) / ro / (1 + ro) ** (n_years + n)
    eo = S.open_tbtu[2031] * (fee29 - S.COST) / 1000 - 1.0 * (1 - share_c)
    pv += eo * (1 - S.TAX) / ro / (1 + ro) ** n_years
    nci = S.NCI * (1 - S.TAX) / rc
    nd = path(fee)[2][4] if roll_to_2028 else S.ND0
    return (pv - nd - S.PREF_LIQ - nci - S.BP) / S.SHARES

def needed(**kw):
    lo, hi = -2.0, 20.0
    for _ in range(60):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if value(m, **kw) < px else (lo, m)
    return m

L = [f"price {px} (close Oct 7 2026)"]
# management framework gap, 2029, at a $3 open fee
con29 = S.vol[2029] - S.open_tbtu[2029]
mine3 = (con29 * S.CONTRACT_FEE[2029] + S.open_tbtu[2029] * 3.0 - S.COST * S.vol[2029]) / 1000
mine5 = mine3 + 2 * S.open_tbtu[2029] / 1000
gap = 11.0 - mine3
L.append(f"2029 EBITDA at a $3 open fee: mine {mine3:.2f} bn vs management 'about 11' -> gap {gap:.2f} bn; at $5: mine {mine5:.2f} vs management 17")
L.append(f"  the gap equals {gap * 1000 / S.vol[2029]:.2f} $/MMBtu on all {S.vol[2029]:.0f} TBtu of 2029 volume, or {gap * 1000 / con29:.2f} on the {con29:.0f} TBtu contracted")
fees = [x / 2 for x in range(0, 17)]
L.append("payoff line: flat open fee from 2029 -> value per share today | end-2028 (my costs, CP2 +0.40) | today (management framework) | today (CP2 fee +0.85)")
rows = []
for f_ in fees:
    a = value(f_, cp2_extra=0.40); b = value(f_, cp2_extra=0.40, roll_to_2028=True); c = value(f_, uplift=gap); d = value(f_, cp2_extra=0.85)
    rows.append((f_, a, b, c, d))
    L.append(f"  {f_:4.1f}  {a:7.2f}  {b:7.2f}  {c:7.2f}  {d:7.2f}")
slope = (value(6.0, cp2_extra=0.40) - value(4.0, cp2_extra=0.40)) / 2
L.append(f"slope: each $1 of long-run open fee is worth {slope:.2f} a share today")
fut_avg = sum(S.jk[y] for y in (2029, 2030, 2031)) / 3
L.append(f"CME futures average 2029-31 (JKM method): {fut_avg:.2f}; VG median 5.19")
for lab, f_ in (("futures avg 2029-31", fut_avg), ("4.50", 4.5), ("VG median 5.19", 5.19)):
    L.append(f"  {lab:<22} today {value(f_):6.2f}  end-2028 {value(f_, roll_to_2028=True):6.2f}  mgmt framework today {value(f_, uplift=gap):6.2f}  CP2 +0.85 today {value(f_, cp2_extra=0.85):6.2f}")
L.append(f"fee the price needs from 2029: my costs {needed():.2f}; management framework {needed(uplift=gap):.2f}; CP2 fees +0.85 {needed(cp2_extra=0.85):.2f}")
CP2C = 0.40
L.append(f"CENTRAL (market-implied open fee {fut_avg:.2f} from 2029, CP2 fees +{CP2C:.2f}): today {value(fut_avg, cp2_extra=CP2C):.2f}, end-2028 {value(fut_avg, cp2_extra=CP2C, roll_to_2028=True):.2f} ({value(fut_avg, cp2_extra=CP2C, roll_to_2028=True) / px - 1:+.0%} vs price); fee the price needs {needed(cp2_extra=CP2C):.2f}")
L.append(f"  at VG's median 5.19 with CP2 +{CP2C:.2f}: today {value(5.19, cp2_extra=CP2C):.2f}, end-2028 {value(5.19, cp2_extra=CP2C, roll_to_2028=True):.2f}")
L.append(f"  same with CP2 fees +0.00: today {value(fut_avg):.2f}, end-2028 {value(fut_avg, roll_to_2028=True):.2f}; with +0.85: today {value(fut_avg, cp2_extra=0.85):.2f}, end-2028 {value(fut_avg, cp2_extra=0.85, roll_to_2028=True):.2f}")
L.append(f"  at VG's median 5.19 with CP2 +0.85: today {value(5.19, cp2_extra=0.85):.2f}, end-2028 {value(5.19, cp2_extra=0.85, roll_to_2028=True):.2f}; management framework at futures: today {value(fut_avg, uplift=gap):.2f}, end-2028 {value(fut_avg, uplift=gap, roll_to_2028=True):.2f}")
# cost run-rate from 2026 actuals
from common import read
fh = {r["item"]: float(r["value"]) for r in read("vg_fee_history.csv")}
for q, eb in (("q1", 3863 - 2491), ("q2", 2491)):
    tb = fh[f"company_{q}_2026_tbtu"]; fe = fh[f"company_{q}_2026_new"]
    L.append(f"2026 {q.upper()}: implied fee margin {tb * fe:.0f}m less adjusted EBITDA {eb}m = costs {tb * fe - eb:.0f}m, {(tb * fe - eb) / tb:.2f}/MMBtu (model uses {S.COST:.2f})")
L.append(f"for management's 'about 11bn at $3' with my volumes and 2.45 contract fee, costs would have to be {(con29 * S.CONTRACT_FEE[2029] + S.open_tbtu[2029] * 3.0 - 11000) / S.vol[2029]:.2f}/MMBtu")
L.append(f"Henry Hub: +$1 on HH = -$1.15 on the open fee = {-1.15 * slope:.2f} a share")
# peer multiple cross-check
for name, fee in (("base (futures to 2029, then 5.19)", {**jk, 2030: 5.19, 2031: 5.19}), ("futures all the way", jk), ("central 4.50", {**jk, 2029: 4.5, 2030: 4.5, 2031: 4.5})):
    p = path(fee)
    for idx, y in ((4, 2030), (5, 2031)):
        e, nd = p[idx][1], p[idx][4]
        for mult in (8.1, 10.3):
            eq = (mult * e - nd - S.PREF_LIQ - S.NCI * (1 - S.TAX) / S.RC - S.BP) / S.SHARES
            L.append(f"multiple check {name:<34} {y}: EBITDA {e:5.2f} x {mult:4.1f} -> {eq:6.2f}/share in {y} (undiscounted)")
out = LEGACY_NOTE + "\n".join(L); print(out)
open(os.path.join(RESULTS, "valuation_v6.txt"), "w").write(out + "\n")
import csv
with open(os.path.join(RESULTS, "payoff_line.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["open_fee_from_2029", "value_today_central_costs_cp2_plus040", "value_end2028_central", "value_today_mgmt_framework", "value_today_cp2_fee_plus085"])
    for r in rows: w.writerow([f"{x:.2f}" for x in r])
