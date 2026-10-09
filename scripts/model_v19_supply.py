"""v19: plant-by-plant LNG supply model and a fundamentals-based answer to the shortage test.

Every input is in data/lng_projects_v19.csv (one row per project, with sources) or cited below.

SUPPLY (Mt) = 0.84 x nameplate - war outages - legacy losses
  nameplate : 524.5 Mtpa operating at end-2025 (IGU WLR 2026) + each project in lng_projects_v19.csv as it
              ramps (40% of nameplate in its first year, linear to 100% by its full year)
              + future FIDs (rule below). 0.84 = IGU 2025 utilisation (83.9%); 0.84 x 524.5 = 441 Mt vs 437 Mt traded.
  outages   : IEA Gas Market Report Q3-2026: war losses ~140 bcm (~103 Mt) over 2026-30, "largely concentrated in
              2026 and 2027"; 2026 = 54 bcm (39.7 Mt). The damaged Ras Laffan trains (12.8 Mtpa) are out for about three
              years (QatarEnergy, Sep 2026): 10.8 Mt in 2028, 8.1 Mt in 2029. The rest of the IEA total, 44.5 Mt, I put in 2027.
  legacy    : to 2030, IEA Gas 2025's feedgas losses at legacy plants (~20 bcm/yr = 14.7 Mt by 2030, phased in
              linearly from 2026); after 2030, the pre-2026 fleet declines d%/yr (0/1/2%, my assumption, bracketed).
FUTURE FIDs (each arrives with first output 4 years after FID, full output after 5):
  empirical  : the industry's own record (IGU WLR 2026): 2021-25 sanctioned 206 Mtpa (41.2/yr) in a tight market;
               2016-20 sanctioned half that (~103 Mtpa, 20.6/yr) through a glut. So 20.6 Mtpa in glut years, 41.2 otherwise.
               From 2027 (2026 FIDs already in the project list). VG's bolt-ons and North Field West sit inside this flow.
  none       : stress test: nothing beyond what is under construction today.
  foresight  : developers sanction exactly enough to balance the market five years out (cap 70 Mtpa/yr, about the
               2019 record and 2025's 68.4 Mtpa).
DEMAND: Shell LNG Outlook 2026 (+65% 2025-2050) and GECF (406 Mt 2024, ~700 Mt 2035, ~785 Mt 2040, slope held after),
        straight lines, both rescaled to IGU's 437 Mt for 2025 so supply and demand use one base; midpoint = average.
DEMAND RESPONSE (central): the IEA (Gas 2025) finds that prices converging to US short-run cost unlock ~65 bcm
        (~48 Mt) more LNG demand by 2030 than its base case. When supply runs more than 5% ahead of reference demand, I
        add that response (scaled with demand, and only down to balance) before classifying. It makes 2028-29 "balanced", matching the futures
        (8.03 and 5.12) better than the no-response version, which calls them glut. No-response is shown as a sensitivity.
REGIMES: glut if supply exceeds demand by more than 5%; shortage if it falls more than 2% short; balanced otherwise.
FEES ($/MMBtu, VG's formula): glut 1.00 (2015-20: 0.45 TTF, 1.62 JKM); shortage 9.60 (2011-14, 2021-22, 2026 average);
        balanced 3.90 (GECF's cost of proposed North American plants, the long-run-marginal-cost anchor IGU says sets
        price once the market rebalances). Free entry means that the cost of new plants already prices in the average
        rent from future shocks, so shocks are not added on top in the central case; the shock overlay
        (a 2-year shortage starting with probability 3/16 in any non-glut year: Fukushima, Russia, Hormuz in 16 years)
        is shown as an upper bound. Sensitivity: balanced pays 7.00, the 2023-25 rebalancing average.
OUTPUT: shortage share and flat-equivalent fee for 2032-2049 (VG's open cargoes, discounted at 10%), against the
        44% shortage share and 4.49 fee that today's price needs.
"""
import os, csv, random
from common import RESULTS, DATA

proj = list(csv.DictReader(open(os.path.join(DATA, "lng_projects_v19.csv"))))
UTIL, BASE, Y0, Y1 = 0.84, 524.5, 2025, 2049
YEARS = range(Y0, Y1 + 1)
OUTAGE = {2026: 39.7, 2027: 44.5, 2028: 12.8 * UTIL, 2029: 12.8 * UTIL * 0.75}
FEEDGAS_2030 = 20 / 1.36                 # IEA: ~20 bcm/yr by 2030; 1 Mt LNG ~ 1.36 bcm
RESPONSE_2030 = 65 / 1.36                # IEA high case: >65 bcm extra demand by 2030
NEED_FEE, NEED_SHARE = 4.49, 0.44
WIN = range(2032, 2050)
DISC = {y: 1.10 ** -(y - 2032) for y in WIN}
HIST_PACE = (20.6, 41.2)                 # IGU: 2016-20 ~103 Mtpa, 2021-25 206 Mtpa sanctioned

def ramp(y, first, full):
    if y < first: return 0.0
    if y >= full: return 1.0
    return 0.4 + 0.6 * (y - first) / (full - first)

def committed_nameplate(y, decline, probable=False):
    legacy = BASE * (1 - decline) ** max(0, y - 2030)
    return legacy + sum(float(p["capacity_mtpa"]) * ramp(y, int(p["first_year"]), int(p["full_year"]))
                        for p in proj if p["first_year"] and ("probable" not in p["status"] or probable))

def legacy_loss(y): return FEEDGAS_2030 * min(1.0, max(0, y - 2025) / 5)

def shell(y): return 437 * (1 + 0.65 * (y - 2025) / 25)
def gecf_raw(y): return 406 + 294 * (y - 2024) / 11 if y <= 2035 else 700 + 17 * (y - 2035)
def gecf(y): return gecf_raw(y) * 437 / gecf_raw(2025)
def mid(y): return (shell(y) + gecf(y)) / 2
DEMAND = {"Shell": shell, "midpoint": mid, "GECF": gecf}

def regime(s): return "glut" if s > 0.05 else ("shortage" if s < -0.02 else "balanced")

def simulate(dem, decline=0.01, rule="pace", pace=30.9, resp=True, probable=False):
    """rule: 'pace' (constant Mtpa/yr from 2027), 'empirical' (20.6 in glut years, 41.2 otherwise),
    'none' (nothing beyond today's list), 'foresight' (balance the market five years out, cap 70/yr)."""
    fids = {}
    def supply(y):
        return UTIL * (committed_nameplate(y, decline, probable) + sum(v * ramp(y, f + 4, f + 5) for f, v in fids.items())) \
               - OUTAGE.get(y, 0) - legacy_loss(y)
    def surplus(y):
        s = supply(y) / dem(y) - 1
        if resp and s > 0.05:   # cheap gas pulls in extra demand, but only down to balance: it cannot create a shortage
            s = max(0.0, supply(y) / (dem(y) + RESPONSE_2030 * dem(y) / dem(2030)) - 1)
        return s
    sur, reg = {}, {}
    for y in YEARS:
        sur[y] = surplus(y); reg[y] = regime(sur[y])
        if y >= 2027:
            if rule == "pace": fids[y] = pace
            elif rule == "empirical": fids[y] = HIST_PACE[0] if reg[y] == "glut" else HIST_PACE[1]
            elif rule == "foresight": fids[y] = min(70.0, max(0.0, (dem(y + 5) - supply(y + 5)) / UTIL))
    return sur, reg, supply

def flat(reg, bal=3.90):
    f = {"glut": 1.00, "balanced": bal, "shortage": 9.60}
    return sum(f[reg[y]] * DISC[y] for y in WIN) / sum(DISC.values())

def shocks(reg, n=3000, seed=7, p=3 / 16, bal=3.90):
    rnd = random.Random(seed); share = fee = hit = 0
    for _ in range(n):
        left, seq = 0, {}
        for y in range(2027, Y1 + 1):
            r = reg[y]
            if left: left -= 1; r = "shortage" if reg[y] != "glut" else r
            elif r != "glut" and rnd.random() < p: left = 1; r = "shortage"
            seq[y] = r
        v = flat(seq, bal); share += sum(seq[y] == "shortage" for y in WIN) / 18; fee += v; hit += v >= NEED_FEE
    return share / n, fee / n, hit / n

def breakeven(dem, dec, resp=True, with_shocks=False):
    f = (lambda r: shocks(r, n=2000)[1]) if with_shocks else flat
    if f(simulate(dem, dec, "pace", 0.0, resp)[1]) < NEED_FEE: return 0.0
    lo, hi = 0.0, 90.0
    for _ in range(18):
        md = (lo + hi) / 2
        if f(simulate(dem, dec, "pace", md, resp)[1]) >= NEED_FEE: lo = md
        else: hi = md
    return lo

L = []
L.append("A. Calibration (midpoint demand, 1% decline, FIDs at 30.9 Mtpa/yr): balance vs what the market paid or prices")
mark = {2025: "fee ~6 (JKM avg 12.16, IGU): rebalancing", 2026: "fee 11-12: shortage", 2027: "futures fee 15.41",
        2028: "futures 8.03", 2029: "futures 5.12", 2030: "futures 3.80", 2031: "futures 2.50"}
s1, r1, sup = simulate(mid); s0, r0, _ = simulate(mid, resp=False)
for y in range(2025, 2032):
    L.append(f"   {y}: supply {sup(y):5.0f} Mt, demand {mid(y):5.0f} | with IEA price response {s1[y]:+4.0%} {r1[y]:<8} | without {s0[y]:+4.0%} {r0[y]:<8} | {mark[y]}")

L.append("B. Supply build, committed projects only (no new FIDs), 1% legacy decline after 2030; surplus before price response")
rows = []
_, _, sup_none = simulate(mid, 0.01, "none", resp=False)
for y in (2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2035, 2040, 2045, 2049):
    s = sup_none(y)
    rows.append([y, round(committed_nameplate(y, 0.01), 1), round(s, 1)] + [round(d(y), 1) for d in DEMAND.values()])
    L.append(f"   {y}: nameplate {committed_nameplate(y, 0.01):5.0f} Mtpa | supply {s:5.0f} Mt | " + " ".join(f"{n} {s / d(y) - 1:+.0%}" for n, d in DEMAND.items()))
with open(os.path.join(RESULTS, "lng_supply_v19.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["year", "committed_nameplate_mtpa", "supply_mt_no_new_fids", "demand_shell", "demand_midpoint", "demand_gecf"]); w.writerows(rows)
recon = sum(float(p["capacity_mtpa"]) for p in proj if p["in_igu_234"] == "yes") + 13.2
L.append(f"   check: rows tagged as inside IGU's 234.3 Mtpa under construction, + Arctic LNG 2's 13.2 = {recon:.1f} Mtpa")

L.append("C. THE TEST: break-even FID pace = the constant Mtpa/yr of new FIDs from 2027 at which the 2032-49 flat fee is exactly 4.49")
L.append(f"   history (IGU): 2016-20 {HIST_PACE[0]} Mtpa/yr through a glut; 2021-25 {HIST_PACE[1]} Mtpa/yr; 2019 record and 2025 (68.4) near 70")
be = []
for name, dem in DEMAND.items():
    for dec in (0.0, 0.01, 0.02):
        a, b, c = breakeven(dem, dec), breakeven(dem, dec, True, True), breakeven(dem, dec, False)
        be.append([name, dec, round(a, 1), round(b, 1), round(c, 1)])
        L.append(f"   {name:<8} decline {dec:.0%}: today's price needs FIDs below {a:4.1f} Mtpa/yr | {b:4.1f} if shocks recur on top | {c:4.1f} without the price response")
with open(os.path.join(RESULTS, "fid_breakeven_v19.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["demand", "legacy_decline", "breakeven_central", "breakeven_with_shocks", "breakeven_no_price_response"]); w.writerows(be)

L.append("D. PROBABILITY: 3 demand paths x 3 decline rates (equal weights) x FID pace uniform between the two historical paces")
paces = [HIST_PACE[0] + (HIST_PACE[1] - HIST_PACE[0]) * i / 40 for i in range(41)]
res = {}
for resp in (True, False):
    n = hit = hit_s = share = fee = fee_s = 0
    for dem in DEMAND.values():
        for dec in (0.0, 0.01, 0.02):
            for p in paces:
                r = simulate(dem, dec, "pace", p, resp)[1]; v = flat(r)
                n += 1; hit += v >= NEED_FEE; fee += v; share += sum(r[y] == "shortage" for y in WIN) / 18
                x = shocks(r, n=400); hit_s += x[2]; fee_s += x[1]
    res[resp] = (hit / n, hit_s / n, share / n, fee / n, fee_s / n)
    L.append(f"   {'with' if resp else 'without'} price response: fee clears 4.49 in {hit / n:.0%} of cases ({hit_s / n:.0%} with shocks on top, mean fee {fee_s / n:.2f});"
             f" mean flat fee {fee / n:.2f}; structural shortage share {share / n:.0%} (price needs 44%)")

L.append("E. Robustness: other FID behaviour, central demand response, 2032-49 flat fee (balanced at 3.90 | at 7.00)")
for rule in ("empirical", "foresight", "none"):
    cells = []
    for name, dem in DEMAND.items():
        r = simulate(dem, 0.01, rule)[1]
        cells.append(f"{name} {flat(r):.2f}|{flat(r, 7.0):.2f} ({sum(r[y] == 'shortage' for y in WIN)} shortage yrs)")
    L.append(f"   {rule:<9}: " + "; ".join(cells))
s, r, _ = simulate(mid, 0.01, "pace", 20.6)
L.append("   central path at the slow pace (midpoint, 1%, 20.6/yr): " + " ".join(f"{y}:{r[y][0].upper()}{s[y]:+.0%}" for y in range(2026, 2050)) + f" -> fee {flat(r):.2f}")
with open(os.path.join(RESULTS, "supply_summary_v19.csv"), "w") as f:
    f.write("item,value\n")
    f.write(f"p_clear_central,{res[True][0]:.4f}\np_clear_shocks,{res[True][1]:.4f}\nshortage_share_central,{res[True][2]:.4f}\n")
    f.write(f"mean_fee_central,{res[True][3]:.4f}\nmean_fee_shocks,{res[True][4]:.4f}\np_clear_noresp,{res[False][0]:.4f}\nmean_fee_noresp,{res[False][3]:.4f}\n")
    f.write(f"breakeven_mid_1pct,{[b for b in be if b[0] == 'midpoint' and b[1] == 0.01][0][2]}\n")
txt = "\n".join(L); print(txt); open(os.path.join(RESULTS, "model_v19_supply.txt"), "w").write(txt + "\n")
