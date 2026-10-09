# Replication check

**v20 (9 Oct 2026):** `python scripts/replicate.py` copies `data/` and `scripts/` to an empty folder, runs 14 model scripts in order and compares every output with the committed `results/`. Result: 37 outputs produced, 37 identical, 0 differ. GitHub Actions runs the same check on every push (`.github/workflows/replicate.yml`), so the badge on the repo shows whether the published numbers still reproduce.

Key numbers to check: value today 8.99, end-2028 11.27, fee needed 4.49 at 13.05; backtest fee curve 3.00 - 46.3 x surplus; odds the 2032-49 fee clears 4.49: 35%; mean model fee 3.12; Hormuz end-2028 13.61.

An independent replication by someone other than me is still worth doing: open an issue with your outputs if anything differs.

## Earlier record

# Replication check

Clean-room run on 8 Oct 2026: the repo zip was unpacked into an empty directory and every script below was run with Python 3.10 and no other inputs. Each output was compared byte for byte with the committed file in `results/`.

```
cd scripts
python model_v10.py
python model_v11_addons.py
python model_v12_addons.py
python model_v13_addons.py
python model_v14_addons.py
python model_v15_addons.py
python model_v17_addons.py
python model_v19_supply.py
python model_v19_addons.py
python bond_check.py
python waterfall.py
python refresh_to_close.py 13.29     # publication-day check at a new close
```

Result: all 15 outputs matched exactly (model_v10.txt, model_v11-v17 add-on outputs, bond_check_v10.txt, waterfall.txt, lrmc_v14.csv, eps_path_v10.csv, scenarios_v10.csv, audit_v10.csv, options_implied_v15.csv, lng_balance_v17.csv).

v19 rerun, 9 Oct 2026: same procedure with the two v19 scripts added; all 28 files written to `results/` matched the committed copies byte for byte. v19 numbers to check: break-even FID pace on midpoint demand at 1% decline 15.1 Mtpa/yr; odds 6% (32% with shocks); CP2 +10% end-2028 10.15.

Key numbers you should get: value today 8.99, end-2028 11.27, fee needed 4.49 at 13.05 (4.55 at 13.29), weighted end-2028 12.04.

This is a self-replication (same author, fresh environment). An independent replication by someone else is still worth doing: open an issue with your outputs if anything differs.
