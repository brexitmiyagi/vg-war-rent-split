"""v20 forward model: plant-by-plant supply (v19 inputs) with the two pieces v19 lacked.

1. A fee curve fitted to history instead of a step function: fee = c + k x surplus, fitted in model_v20_backtest.py
   on 2015-2025 without the 2021-22 outside shock (results/fee_curve_v20.csv). Floored at $0 (below that, US cargoes
   get cancelled, as in 2020) and capped at $9.60 (the 2011-26 shortage average) for structural tightness.
2. Approvals that respond to prices: new FIDs in year t = a + b x fee in t-1 (results/fid_response_v20.csv:
   ~25 Mtpa/yr after cheap years, ~41 after expensive ones, IGU 2016-2025), bounded 0-70 Mtpa (the 2019 record).
   First output 4 years after FID, full output after 5. 2026 approvals are already in the project list.
Shocks: a two-year outside shock (Russia-, Hormuz-, Fukushima-type) starts with probability 3/16 in any year whose
   structural surplus is 5% or less; the fee in shock years is at least $9.60. The backtest shows these shocks are real
   and sit outside the LNG balance (it missed 2021-22), so they are part of the central case, not an add-on.
Demand: Shell, GECF and their midpoint (rebased to IGU's 437 Mt for 2025); IEA price response optional (chosen by
   which version tracks the 2028-31 futures better).
Scenarios: central; prolonged Hormuz (Gulf exports at 25% of normal through 2027 and 50% in 2028; damaged Ras Laffan
   trains back in 2030, not 2029; North Field East and South two years late).
Output: 2032-49 flat-equivalent fee on VG's open cargoes (10% discount) - distribution, mean, P(>= $4.49);
   break-even constant approval pace; the 2027-31 fee path vs the futures.
"""
import os, csv, random, io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import model_v19_supply as S
from common import RESULTS

fc = {r["item"]: float(r["value"]) for r in csv.DictReader(open(os.path.join(RESULTS, "fee_curve_v20.csv")))}
fr = {r["item"]: float(r["value"]) for r in csv.DictReader(open(os.path.join(RESULTS, "fid_response_v20.csv")))}
C, K, A, B = fc["intercept"], fc["slope_per_unit_surplus"], fr["intercept"], fr["slope_per_usd_fee"]
CAP, FLOOR, SHOCK_FEE, P_SHOCK = 9.60, 0.0, 9.60, 3 / 16
NEED = 4.49
WIN = range(2032, 2050); DISC = {y: 1.10 ** -(y - 2032) for y in WIN}; DSUM = sum(DISC.values())
FUT = {2027: 15.41, 2028: 8.03, 2029: 5.12, 2030: 3.80, 2031: 2.50}
GULF = 81.51 + 5.6          # Qatar 2025 exports (IGU WLR 2026) + UAE Das Island (~5.6 Mtpa); scenario base
FEE_2026 = 10.81            # 2026 Jan-Sep fee, TTF basis (data/fred_ttf_hh_monthly.csv)

DELTA = 0.0                 # market calibration offset, set below
def fee_of(s): return min(CAP, max(FLOOR, C + K * (s - DELTA)))

def outages(y, hormuz):
    if not hormuz: return S.OUTAGE.get(y, 0.0)
    return {2026: 39.7, 2027: 0.75 * GULF, 2028: 0.50 * GULF, 2029: 12.8 * S.UTIL}.get(y, 0.0)

def nameplate(y, decline, hormuz):
    if not hormuz: return S.committed_nameplate(y, decline)
    legacy = S.BASE * (1 - decline) ** max(0, y - 2030); tot = legacy
    for p in S.proj:
        if not p["first_year"] or "probable" in p["status"]: continue
        f0, f1 = int(p["first_year"]), int(p["full_year"])
        if p["project"].startswith("Qatar North Field"): f0, f1 = f0 + 2, f1 + 2
        tot += float(p["capacity_mtpa"]) * S.ramp(y, f0, f1)
    return tot

def path(dem, decline=0.01, resp=False, hormuz=False, rnd=None, pace=None):
    """one simulated path; rnd=None -> no shocks. pace=None -> price-responsive approvals; else constant pace."""
    fids, fee, sur, left, prev = {}, {}, {}, 0, FEE_2026
    for y in range(2025, 2050):
        sup = S.UTIL * (nameplate(y, decline, hormuz) + sum(v * S.ramp(y, f + 4, f + 5) for f, v in fids.items())) - outages(y, hormuz) - S.legacy_loss(y)
        s = sup / dem(y) - 1
        if resp and s > 0.05: s = max(0.0, sup / (dem(y) + S.RESPONSE_2030 * dem(y) / dem(2030)) - 1)
        f = fee_of(s)
        if rnd is not None and y >= 2027:
            if left: left -= 1; f = max(f, SHOCK_FEE)
            elif s <= 0.05 and rnd.random() < P_SHOCK: left = 1; f = max(f, SHOCK_FEE)
        sur[y], fee[y] = s, f
        if y >= 2027: fids[y] = pace if pace is not None else min(70.0, max(0.0, A + B * prev))
        prev = f
    return fee, sur, fids

def flat(fee): return sum(fee[y] * DISC[y] for y in WIN) / DSUM

L = []
L.append(f"Inputs: fee curve {C:.2f} {K:+.1f} x surplus (R^2 {fc['r2']:.2f}); approvals {A:.1f} + {B:.2f} x last year's fee")
L.append("A. Calibration against the futures (midpoint demand, 1% decline, no shocks): model fee 2027-31 vs CME implied fee")
best = None
for resp in (False, True):
    fee, sur, _ = path(S.mid, 0.01, resp)
    err = sum((fee[y] - FUT[y]) ** 2 for y in range(2028, 2032)) ** 0.5
    L.append(f"   {'with' if resp else 'without'} IEA price response: " + " ".join(f"{y} {fee[y]:.2f} ({sur[y]:+.0%})" for y in range(2027, 2032)) + f" | futures " + " ".join(f"{FUT[y]:.2f}" for y in range(2027, 2032)) + f" | error 2028-31 {err:.2f}")
    if best is None or err < best[0]: best = (err, resp)
RESP = best[1]
L.append(f"   central uses the {'with' if RESP else 'without'}-response version (closer to the futures)")
# market calibration: the history-fitted curve on my plant-by-plant build is far below the futures for 2028-31, so I
# find the surplus offset that makes the model match the CME strip there (the market's view of delays, slower ramps
# and stronger demand than my build assumes) and keep it for every later year.
def calib_err(d):
    global DELTA
    DELTA = d; fee = path(S.mid, 0.01, RESP)[0]; DELTA = 0.0
    return sum((fee[y] - FUT[y]) ** 2 for y in range(2028, 2032)) ** 0.5
grid = [i / 1000 for i in range(0, 201)]
DELTA_CAL = min(grid, key=calib_err)
DELTA = DELTA_CAL
fee_c = path(S.mid, 0.01, RESP)[0]
L.append(f"   market-calibrated offset: {DELTA:.3f} (supply effectively {DELTA:.1%} tighter than my build); model 2027-31 " + " ".join(f"{fee_c[y]:.2f}" for y in range(2027, 2032)) + f"; error {calib_err(DELTA):.2f}")
DELTA = DELTA_CAL

def run(dem, dec, hormuz=False, n=2000, seed=11):
    rnd = random.Random(seed); fl = []
    for _ in range(n):
        fee, sur, fids = path(dem, dec, RESP, hormuz, rnd); fl.append(flat(fee))
    det_fee, det_sur, det_fids = path(dem, dec, RESP, hormuz)
    fl.sort()
    return dict(mean=sum(fl) / n, p=sum(f >= NEED for f in fl) / n, p10=fl[int(0.1 * n)], p50=fl[n // 2], p90=fl[int(0.9 * n)],
                det=flat(det_fee), fids=sum(det_fids.get(y, 0) for y in range(2027, 2045)) / 18, fee=det_fee, sur=det_sur)

L.append("B. 2032-49 flat fee on open cargoes, price-responsive approvals, shocks at the 2011-26 rate (2,000 paths each)")
rows, agg = [], {}
for scen in (False, True):
    for name, dem in S.DEMAND.items():
        for dec in (0.0, 0.01, 0.02):
            r = run(dem, dec, scen); agg[(scen, name, dec)] = r
            rows.append([("hormuz" if scen else "central"), name, dec, round(r["det"], 2), round(r["mean"], 2), round(r["p10"], 2), round(r["p50"], 2), round(r["p90"], 2), round(r["p"], 3), round(r["fids"], 1)])
            L.append(f"   {'Hormuz ' if scen else 'central'} {name:<8} decline {dec:.0%}: no-shock fee {r['det']:.2f} | with shocks mean {r['mean']:.2f} (10-90%: {r['p10']:.2f}-{r['p90']:.2f}) | P(>=4.49) {r['p']:.0%} | approvals avg {r['fids']:.0f} Mtpa/yr")
with open(os.path.join(RESULTS, "supply_v20.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["scenario", "demand", "legacy_decline", "flat_fee_no_shocks", "flat_fee_mean", "p10", "p50", "p90", "p_fee_ge_4.49", "avg_fids_mtpa"]); w.writerows(rows)
summ = {}
for scen in (False, True):
    g = [v for k, v in agg.items() if k[0] == scen]
    summ[scen] = (sum(v["mean"] for v in g) / 9, sum(v["p"] for v in g) / 9, sum(v["det"] for v in g) / 9, min(v["p"] for v in g), max(v["p"] for v in g))
    L.append(f"   {'HORMUZ' if scen else 'CENTRAL'} (9 cases equal weight): mean flat fee {summ[scen][0]:.2f} (no shocks {summ[scen][2]:.2f}); P(fee >= 4.49) {summ[scen][1]:.0%} (range across cases {summ[scen][3]:.0%}-{summ[scen][4]:.0%})")
c = agg[(False, "midpoint", 0.01)]
L.append("   central path (midpoint, 1%, no shocks): " + " ".join(f"{y}:{c['fee'][y]:.1f}" for y in range(2026, 2050, 2)))

L.append("C. Break-even constant approval pace (fee curve, shocks on, 1,000 paths): pace at which the 2032-49 mean flat fee = 4.49")
be = []
for name, dem in S.DEMAND.items():
    for dec in (0.0, 0.01, 0.02):
        def mf(p):
            rnd = random.Random(5); return sum(flat(path(dem, dec, RESP, False, rnd, pace=p)[0]) for _ in range(600)) / 600
        def mf0(p): return flat(path(dem, dec, RESP, False, None, pace=p)[0])
        out = []
        for fn in (mf0, mf):
            if fn(0.0) < NEED: out.append(0.0); continue
            lo, hi = 0.0, 90.0
            for _ in range(14):
                md = (lo + hi) / 2
                lo, hi = (md, hi) if fn(md) >= NEED else (lo, md)
            out.append(lo)
        be.append([name, dec, round(out[0], 1), round(out[1], 1)])
        L.append(f"   {name:<8} decline {dec:.0%}: price needs approvals below {out[0]:4.1f} Mtpa/yr without shocks, {out[1]:4.1f} with shocks")
with open(os.path.join(RESULTS, "fid_breakeven_v20.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["demand", "legacy_decline", "breakeven_no_shocks", "breakeven_with_shocks"]); w.writerows(be)
# history-only sensitivity (no market calibration)
_d = DELTA; DELTA = 0.0
hist_only = [run(dem, dec, False, n=600) for dem in S.DEMAND.values() for dec in (0.0, 0.01, 0.02)]
DELTA = _d
ho_mean = sum(r["mean"] for r in hist_only) / 9; ho_p = sum(r["p"] for r in hist_only) / 9
L.append(f"   sensitivity, history-fitted curve without market calibration: mean flat fee {ho_mean:.2f}, P(>=4.49) {ho_p:.0%}")
hz = path(S.mid, 0.01, RESP, True)[0]
L.append("D. Hormuz scenario fee path (midpoint, no shocks): " + " ".join(f"{y} {hz[y]:.2f}" for y in range(2027, 2032)) + " vs futures " + " ".join(f"{FUT[y]:.2f}" for y in range(2027, 2032)))
with open(os.path.join(RESULTS, "supply_summary_v20.csv"), "w") as f:
    f.write("item,value\n")
    f.write(f"mean_fee_central,{summ[False][0]:.4f}\np_central,{summ[False][1]:.4f}\nmean_fee_noshock_central,{summ[False][2]:.4f}\n")
    f.write(f"p_central_min,{summ[False][3]:.4f}\np_central_max,{summ[False][4]:.4f}\nmean_fee_hormuz,{summ[True][0]:.4f}\np_hormuz,{summ[True][1]:.4f}\n")
    for y in range(2027, 2032): f.write(f"hormuz_fee_{y},{hz[y]:.4f}\n")
    for y in range(2027, 2050): f.write(f"central_fee_{y},{fee_c[y]:.4f}\n")
    mid = [b for b in be if b[0] == "midpoint"]
    f.write(f"be_mid_noshock_lo,{min(b[2] for b in mid)}\nbe_mid_noshock_hi,{max(b[2] for b in mid)}\nbe_mid_shock_lo,{min(b[3] for b in mid)}\nbe_mid_shock_hi,{max(b[3] for b in mid)}\n")
    f.write(f"be_mid_1pct_noshock,{[b for b in mid if b[1] == 0.01][0][2]}\nbe_mid_1pct_shock,{[b for b in mid if b[1] == 0.01][0][3]}\n")
    f.write(f"resp_used,{int(RESP)}\ndelta,{DELTA:.4f}\nhist_only_mean,{ho_mean:.4f}\nhist_only_p,{ho_p:.4f}\n")
txt = "\n".join(L); print(txt); open(os.path.join(RESULTS, "model_v20_supply.txt"), "w").write(txt + "\n")
