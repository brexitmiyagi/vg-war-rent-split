"""Clean-room replication: copy data/ and scripts/ to an empty folder, run every model script in order,
and compare each output byte for byte with the committed file in results/. Exit code 1 on any mismatch.
Usage: python scripts/replicate.py   (standard library only, Python 3.10+)
"""
import os, sys, shutil, subprocess, tempfile, filecmp
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = ["model_v10.py", "model_v11_addons.py", "model_v12_addons.py", "model_v13_addons.py", "model_v14_addons.py",
         "model_v15_addons.py", "model_v17_addons.py", "model_v19_supply.py", "model_v19_addons.py",
         "model_v20_backtest.py", "model_v20_supply.py", "model_v20_addons.py", "bond_check.py", "waterfall.py"]
tmp = tempfile.mkdtemp(prefix="vg_replicate_")
for d in ("data", "scripts"):
    shutil.copytree(os.path.join(ROOT, d), os.path.join(tmp, d), ignore=shutil.ignore_patterns("__pycache__"))
os.makedirs(os.path.join(tmp, "results"))
for s in ORDER:
    r = subprocess.run([sys.executable, s], cwd=os.path.join(tmp, "scripts"), capture_output=True, text=True)
    print(f"{'ran' if r.returncode == 0 else 'FAILED'}  {s}")
    if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
new = sorted(os.listdir(os.path.join(tmp, "results")))
bad = [f for f in new if not os.path.exists(os.path.join(ROOT, "results", f)) or not filecmp.cmp(os.path.join(tmp, "results", f), os.path.join(ROOT, "results", f), shallow=False)]
print(f"\n{len(new)} outputs produced; {len(new) - len(bad)} identical to the committed results/; {len(bad)} differ")
for f in bad: print("  DIFFERS:", f)
shutil.rmtree(tmp)
sys.exit(1 if bad else 0)
