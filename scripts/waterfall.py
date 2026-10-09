"""Where the cash sits: a simplified cash waterfall, 2027-2031, on the central fee path
(v10: CME futures of 7 Oct 2026 for every year to 2031).

What is from documents (data/cp2_restricted_payment_terms.csv, data/debt_by_entity_2026-06-30.csv):
- CP2 can only pay its owner once BOTH phases are complete, its debt service reserve is full, and
  historical and fixed-fee projected DSCR are each at least 1.25x (CTA s.11.1). The fixed-fee test
  counts only the fixed liquefaction fee on its long-term SPAs.
- Before that, CP2 commissioning cash goes to CP2's own construction costs and lenders; payments to
  the owner are allowed only if remaining project costs are already covered (CTA s.11.3).
- Volumes above each plant's nameplate go to VG Commodities (VGC) under intercompany SPAs (10-K).
- CP2's lenders sized the debt at a 1.40x blended DSCR on fixed fees (CTA, Sizing Case DSCR).

What is mine (ASSUMPTION):
- Which open volume is CP2 or expansion commissioning (ring-fenced) and which is VGC excess.
- CP2 Phase 2 completion in 2H 2030 (IEA date), so no CP2 distributions before 2031.
- Interest rates by entity, and treating project notes as interest-only (they are bullets).
- Back-solving CP2's fixed fee from the lender sizing uses an 18-year amortization and 6.5% rate.
"""
import os, io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import sotp as S
    import model_v10 as M
from common import read, RESULTS

debt = {r["entity"] + "|" + r["instrument"]: float(r["usd_m"]) / 1000 for r in read("debt_by_entity_2026-06-30.csv")}
fee = dict(S.jk)                                   # v8 central: CME futures (7 Oct) for every year to 2031
VGC_EXCESS = {2027: 62 + 300, 2028: 62 + 416, 2029: 62 + 416, 2030: 62 + 416, 2031: None}   # TBtu, ASSUMPTION
L = []
L.append("year  open TBtu  ring-fenced (CP2/expansion pre-completion)  VGC excess  share ring-fenced  open margin $bn  of which ring-fenced $bn")
for y in S.YEARS:
    op = S.open_tbtu[y]
    vgc = op if VGC_EXCESS[y] is None else min(op, VGC_EXCESS[y])
    ring = op - vgc
    if y == 2030:   # CP2 Phase 2 completes in 2H 2030: count half the year as pre-completion
        ring *= 0.5; vgc = op - ring
    m = op * (fee[y] - M.C_EX) / 1000
    L.append(f"{y}  {op:9.0f}  {ring:40.0f}  {vgc:10.0f}  {ring / op:17.0%}  {m:15.2f}  {ring * (fee[y] - M.C_EX) / 1000:22.2f}")

# parent-level fixed charges
vglng = debt["VGLNG (parent holdco)|senior secured notes 2029-2036"]
parent_interest = vglng * 0.0838           # blended coupon after the June 2026 refinancing (data/debt_maturities_liquidity_2026-06-30.csv)
from valuation import PREF as pref
common_div = 0.04 * 4 * 2.498              # $0.04 a quarter (Q2 2026 call) on 2.498bn Class A + B shares
L.append(f"parent fixed charges a year: VGLNG interest ~{parent_interest:.2f} (8.38% blended on {vglng:.1f}bn), preferred {pref:.2f}, common dividend at $0.04/qtr {common_div:.2f} -> {parent_interest + pref + common_div:.2f} bn")

# cash that can reach the parent in 2028-2029: VGC excess margin + Calcasieu/Plaquemines contracted margin after project interest
calc_debt = debt["Calcasieu (VGCP)|senior secured notes"] + debt["Calcasieu Funding|term loan B due 2033"]
plaq_debt = debt["Plaquemines (VGPL)|senior secured notes"] + debt["Plaquemines|credit facilities due 2029"]
for y in (2028, 2029):
    vgc = min(S.open_tbtu[y], VGC_EXCESS[y])
    vgc_m = vgc * (fee[y] - M.C_EX) / 1000
    calc_m = 520 * (2.36 - M.C_EX) / 1000
    plaq_m = 1040 * (S.CONTRACT_FEE[y] - M.C_EX) / 1000 - M.BASIS[y]
    proj_int = calc_debt * 0.06 + plaq_debt * 0.065       # ASSUMPTION
    to_parent = vgc_m + max(0.0, calc_m + plaq_m - proj_int)
    L.append(f"{y}: cash able to reach the parent before tax ~{to_parent:.2f} bn (VGC excess {vgc_m:.2f}, Calcasieu+Plaquemines contracted after project interest {max(0.0, calc_m + plaq_m - proj_int):.2f}) vs consolidated EBITDA in the model {M.series(M.L_CENTRAL)[0][y]['ebitda']:.2f}")

# maturity wall and parent liquidity
ml = {r["item"]: r for r in read("debt_maturities_liquidity_2026-06-30.csv")}
wall = [("CP2 Holdings equity bridge loans", 2028), ("Plaquemines credit facilities", 2029), ("VGLNG senior secured notes (2029-2032 series; the 2028s were refinanced in June 2026)", "2029-32")]
tot = 0.0
L.append("maturity wall 2028-2032 (excluding project bonds that also fall due in the window):")
for name, yr in wall:
    v = float(ml[name]["usd_m"]) / 1000; tot += v
    L.append(f"  {yr}: {name} {v:.2f}bn")
L.append(f"  total {tot:.2f}bn; VGCP notes (5.5bn, 2029-2036) and VGPL notes (9.5bn, 2030-2036) also start maturing in this window")
L.append(f"parent liquidity: VGLNG revolver {float(ml['VGLNG revolving credit facility (undrawn)']['usd_m']) / 1000:.1f}bn undrawn (2030), 364-day revolver {float(ml['VGLNG 364-day senior secured revolver']['usd_m']) / 1000:.1f}bn (signed 2 Sep 2026, runs to 2027), consolidated cash {float(ml['cash and cash equivalents (consolidated)']['usd_m']) / 1000:.2f}bn at 30 Jun")

# what CP2's lenders' sizing implies about its fixed fee
cp2_total, rate, n = 20.7, 0.065, 18
annuity = cp2_total * rate / (1 - (1 + rate) ** -n)
cfads_needed = 1.40 * annuity
cp2_tbtu = 18.5 * 52            # CP2 third-party SPAs 18.5 MTPA (Q1 2026 deck slide 23)
L.append(f"CP2 lender sizing: {cp2_total}bn at {rate:.1%} over {n} years = {annuity:.2f}bn debt service a year; at 1.40x the fixed-fee cash flow must be {cfads_needed:.2f}bn")
for opex in (0.4, 0.6, 0.8):
    L.append(f"  on {cp2_tbtu} TBtu of CP2 SPA volume (18.5 MTPA) that needs a fixed fee of about {cfads_needed * 1000 / cp2_tbtu + opex:.2f} with fixed opex {opex:.2f}/MMBtu (my model uses 2.45)")
out = "\n".join(L); print(out)
open(os.path.join(RESULTS, "waterfall.txt"), "w").write(out + "\n")
