import csv, os
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
RESULTS = os.path.join(HERE, "..", "results")
os.makedirs(RESULTS, exist_ok=True)

def read(name):
    with open(os.path.join(DATA, name), newline="") as f:
        return list(csv.DictReader(f))

EURUSD = 1.1177          # ECB reference rate, 7 Oct 2026 (v7 used 1.1269, 6 Oct). I use it for every year.
CURVE_FILE = "cme_settlements_2026-10-07.csv"   # v8; v7 used 2026-10-06 and an earlier run 2026-10-02, both kept in data/
MWH_PER_MMBTU = 3.412    # 1 MWh = 3.412 MMBtu
SHIP_REGAS = 2.0         # Venture Global's own assumption on slide 12
HH_MULT = 1.15           # feed gas is billed at 115% of Henry Hub

def annual_curve():
    """Calendar-year averages of the CME settlements in CURVE_FILE."""
    out = {}
    for r in read(CURVE_FILE):
        y = 2000 + int(r["month"].split()[1])
        d = out.setdefault(y, {"ttf": [], "hh": [], "jkm": []})
        d["ttf"].append(float(r["ttf_eur_mwh"]))
        d["hh"].append(float(r["henry_hub_usd_mmbtu"]))
        d["jkm"].append(float(r["jkm_usd_mmbtu"]))
    return {y: {k: sum(v) / len(v) for k, v in d.items()} for y, d in out.items()}

def fee_jkm(c):
    # the same formula Venture Global uses for its 2010-2026 fee history
    return c["jkm"] - HH_MULT * c["hh"] - SHIP_REGAS

def fee_ttf(c):
    return c["ttf"] / MWH_PER_MMBTU * EURUSD - HH_MULT * c["hh"] - SHIP_REGAS

PRICE_KEY = "share_price_2026-10-07"   # VG close used throughout (13.05); earlier runs used 10-02 and 10-06

def jkm_monthly():
    """IMF Asia LNG (spot, daily-averaged from 2017; tracks JKM) by month, plus my September 2026 estimate."""
    return {r["month"]: float(r["jkm_usd_mmbtu"]) for r in read("jkm_imf_monthly.csv")}
