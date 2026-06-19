"""Build ONE manifest_spec row (idx=$1) if its HDF5 is missing/corrupt; else skip fast
(checks existence BEFORE loading the cutout, so already-built rows exit in <5 s)."""
import sys
from pathlib import Path
import pandas as pd, h5py
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, "/scratch/tsingh65/m61-tng/scripts")
import movie_config as C
r = pd.read_csv(C.REPO_ROOT / "manifest_spec.csv").iloc[int(sys.argv[1])]
def ok(p):
    if not Path(p).exists(): return False
    try:
        h5py.File(p, "r").close(); return True
    except Exception:
        return False
if ok(r.h5):
    print(f"[skip] {Path(r.h5).name}"); sys.exit(0)
import movie_geom as G, movie_spectra as S, yt, trident
yt.set_log_level(40)
tokens = S.validate_tokens(verbose=False)
ds = yt.load(C.CUTOUT); trident.add_ion_fields(ds, ions=C.SPECTRA_ION_LIST, ftype="gas")
vb = G.view_basis(float(r.inc_deg), float(r.alpha_deg), mode=C.MODE)
sl = G.sightline(vb, float(r.rho_kpc))
ray_h5 = str(C.RAY_DIR / r.segment / (Path(r.h5).stem + "_ray.h5"))
Path(ray_h5).parent.mkdir(parents=True, exist_ok=True)
S.build_ray(ds, sl["start_ckpch"], sl["end_ckpch"], ray_h5)
S.generate_movie_spectra(yt.load(ray_h5), vb["v_sys"], r.h5, tokens,
    meta=dict(rho_kpc=float(r.rho_kpc), inc_deg=float(r.inc_deg), alpha_deg=float(r.alpha_deg)))
print(f"[built] {Path(r.h5).name}")
