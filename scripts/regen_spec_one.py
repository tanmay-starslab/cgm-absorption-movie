"""Regenerate ONE manifest_spec row's spectra (idx=$1) by REUSING the existing ray.

Loads the already-built Trident ray, (re)adds the current ion fields onto it, and writes
the 10-ion velocity spectra to the row's h5 (which CGM_SPEC_DIR can point at a fresh dir,
so the original spectra are left untouched). Falls back to building the ray if missing.
Skips fast if the target h5 already exists and is valid."""
import os, sys
from pathlib import Path
import pandas as pd, h5py
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, os.environ.get("CGM_ORIENT_DIR", ""))
import movie_config as C
r = pd.read_csv(C.REPO_ROOT / "manifest_spec.csv").iloc[int(sys.argv[1])]

def ok(p):
    if not Path(p).exists(): return False
    try: h5py.File(p, "r").close(); return True
    except Exception: return False

if ok(r.h5):
    print(f"[skip] {Path(r.h5).name}"); sys.exit(0)

import movie_geom as G, movie_spectra as S, yt, trident
yt.set_log_level(40)
tokens = S.validate_tokens(verbose=False)
vb = G.view_basis(float(r.inc_deg), float(r.alpha_deg), mode=C.MODE)
ray_h5 = str(C.RAY_DIR / r.segment / (Path(r.h5).stem + "_ray.h5"))

if Path(ray_h5).exists():                       # FAST PATH: reuse the expensive ray
    ray_ds = yt.load(ray_h5)
    trident.add_ion_fields(ray_ds, ions=C.SPECTRA_ION_LIST, ftype="gas")
    src = "reused-ray"
else:                                           # fallback: build it (needs the cutout)
    sl = G.sightline(vb, float(r.rho_kpc))
    Path(ray_h5).parent.mkdir(parents=True, exist_ok=True)
    ds = yt.load(C.CUTOUT); trident.add_ion_fields(ds, ions=C.SPECTRA_ION_LIST, ftype="gas")
    S.build_ray(ds, sl["start_ckpch"], sl["end_ckpch"], ray_h5)
    ray_ds = yt.load(ray_h5); src = "built-ray"

S.generate_movie_spectra(ray_ds, vb["v_sys"], r.h5, tokens,
    meta=dict(rho_kpc=float(r.rho_kpc), inc_deg=float(r.inc_deg), alpha_deg=float(r.alpha_deg)))
print(f"[{src}] {Path(r.h5).name}")
