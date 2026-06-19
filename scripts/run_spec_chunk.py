"""Build rays+spectra for a contiguous chunk of manifest_spec.csv. Args: chunk_idx nchunks."""
import os, sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, os.environ.get("CGM_ORIENT_DIR", ""))  # orient_m61, pm_general
import movie_config as C, movie_geom as G, movie_spectra as S
chunk = int(sys.argv[1]); nchunks = int(sys.argv[2])
df = pd.read_csv(C.REPO_ROOT / "manifest_spec.csv")
rows = df.iloc[chunk::nchunks]      # strided so each chunk spans all segments
import yt, trident; yt.set_log_level(40)
t0 = time.time(); tokens = S.validate_tokens(verbose=False)
print(f"chunk {chunk}/{nchunks}: {len(rows)} sightlines; loading cutout..."); 
ds = yt.load(C.CUTOUT); trident.add_ion_fields(ds, ions=C.SPECTRA_ION_LIST, ftype="gas")
for _, r in rows.iterrows():
    if Path(r.h5).exists():
        try: __import__("h5py").File(r.h5, "r").close(); print(f"  [skip] {Path(r.h5).name}"); continue
        except Exception: pass
    vb = G.view_basis(float(r.inc_deg), float(r.alpha_deg), mode=C.MODE)
    sl = G.sightline(vb, float(r.rho_kpc))
    ray_h5 = str(C.RAY_DIR / r.segment / (Path(r.h5).stem + "_ray.h5"))
    Path(ray_h5).parent.mkdir(parents=True, exist_ok=True)
    S.build_ray(ds, sl["start_ckpch"], sl["end_ckpch"], ray_h5)
    ray_ds = yt.load(ray_h5)
    S.generate_movie_spectra(ray_ds, vb["v_sys"], r.h5, tokens,
        meta=dict(rho_kpc=float(r.rho_kpc), inc_deg=float(r.inc_deg), alpha_deg=float(r.alpha_deg)))
    print(f"  [ok] {Path(r.h5).name} (t={time.time()-t0:.0f}s)")
print(f"chunk {chunk} done ({time.time()-t0:.0f}s)")
