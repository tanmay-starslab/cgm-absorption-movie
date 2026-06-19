"""Build any manifest_spec rows whose HDF5 is missing (cutout loaded once)."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd, h5py
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, "/scratch/tsingh65/m61-tng/scripts")
import movie_config as C, movie_geom as G, movie_spectra as S
df = pd.read_csv(C.REPO_ROOT / "manifest_spec.csv")
def ok(p):
    if not Path(p).exists(): return False
    try: h5py.File(p, "r").close(); return True
    except Exception: return False
miss = df[~df.h5.map(ok)]
print(f"missing spectra: {len(miss)}")
if len(miss) == 0: sys.exit(0)
import yt, trident; yt.set_log_level(40); t0 = time.time()
tokens = S.validate_tokens(verbose=False)
ds = yt.load(C.CUTOUT); trident.add_ion_fields(ds, ions=C.SPECTRA_ION_LIST, ftype="gas")
for _, r in miss.iterrows():
    vb = G.view_basis(float(r.inc_deg), float(r.alpha_deg), mode=C.MODE)
    sl = G.sightline(vb, float(r.rho_kpc))
    ray_h5 = str(C.RAY_DIR / r.segment / (Path(r.h5).stem + "_ray.h5")); Path(ray_h5).parent.mkdir(parents=True, exist_ok=True)
    S.build_ray(ds, sl["start_ckpch"], sl["end_ckpch"], ray_h5)
    S.generate_movie_spectra(yt.load(ray_h5), vb["v_sys"], r.h5, tokens,
        meta=dict(rho_kpc=float(r.rho_kpc), inc_deg=float(r.inc_deg), alpha_deg=float(r.alpha_deg)))
    print(f"  built {Path(r.h5).name} (t={time.time()-t0:.0f}s)")
print("repair done")
