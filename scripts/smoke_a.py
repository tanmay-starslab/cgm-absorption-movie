"""SMOKE TEST A — spectra. Build the fiducial sightline ray, generate 10 ion velocity
spectra, render the stack, and report: token resolution, S XIV field + signal, v_sys, usetex.
"""
from __future__ import annotations
import os, sys, time, json
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, os.environ.get("CGM_ORIENT_DIR", ""))  # orient_m61, pm_general
import movie_config as C
import movie_geom as G
import movie_spectra as S

OUT = C.RESULTS / "smoke"
OUT.mkdir(parents=True, exist_ok=True)

def main():
    t0 = time.time()
    print("=== SMOKE A: spectra ===")
    # 1) token validation
    tokens = S.validate_tokens(verbose=True)

    # 2) fiducial sightline geometry
    rho = 25.558333340264905
    vb = G.view_basis(C.OBS_INC_DEG, 0.0, mode="noflip")
    sl = G.sightline(vb, rho)
    v_sys = vb["v_sys"]
    print(f"\nFiducial: rho={rho:.2f} kpc inc={C.OBS_INC_DEG} alpha=0 mode=noflip")
    print(f"  v_sys_los = {v_sys:+.3f} km/s   los={vb['los'].round(4)}")
    print(f"  start_ckpch={sl['start_ckpch'].round(1)}  end_ckpch={sl['end_ckpch'].round(1)}")

    # 3) load cutout, build ray
    import yt, trident
    yt.set_log_level(40)
    print(f"\nLoading cutout (t={time.time()-t0:.0f}s)...")
    ds = yt.load(C.CUTOUT)
    print(f"  adding ion fields {C.SPECTRA_ION_LIST} ...")
    trident.add_ion_fields(ds, ions=C.SPECTRA_ION_LIST, ftype="gas")
    # confirm S XIV field exists + its max number density along a quick check
    sxiv_field = ("gas", "S_p13_number_density")
    has_sxiv = sxiv_field in ds.derived_field_list
    print(f"  S XIV field present: {has_sxiv}")

    ray_h5 = OUT / "smokeA_ray.h5"
    print(f"  building ray (t={time.time()-t0:.0f}s)...")
    S.build_ray(ds, sl["start_ckpch"], sl["end_ckpch"], ray_h5)
    ray_ds = yt.load(str(ray_h5))

    # quick S XIV column along the ray
    try:
        nS = np.asarray(ray_ds.r[sxiv_field]); dl = np.asarray(ray_ds.r[("gas", "dl")].to("cm"))
        NS = float(np.sum(nS * dl))
        print(f"  S XIV column along ray ~ {NS:.3e} cm^-2")
    except Exception as e:
        NS = float("nan"); print(f"  (S XIV column check skipped: {e})")

    # 4) spectra
    spec_h5 = OUT / "smokeA_spectra.h5"
    print(f"  generating spectra (t={time.time()-t0:.0f}s)...")
    diag = S.generate_movie_spectra(ray_ds, v_sys, spec_h5, tokens,
                                    meta=dict(rho_kpc=rho, inc_deg=C.OBS_INC_DEG, alpha_deg=0.0))
    print("\n  per-ion [min flux in +/-1200, max tau]:")
    for d in C.IONS:
        mn, tx = diag[d["key"]]
        flag = "FLAT" if (np.isfinite(mn) and mn > 0.97) else "absorb"
        print(f"    {d['key']:14s} minflux={mn:.3f}  maxtau={tx:.2e}  [{flag}]")

    # 5) render stack (usetex), with mathtext fallback
    import render_spectra_panel as R
    png = OUT / "smokeA_spectra_stack.png"
    try:
        R.render_spectra_panel(str(spec_h5), str(png), usetex=True)
        used_tex = True
    except Exception as e:
        print(f"  usetex render failed ({e}); falling back to mathtext")
        R.render_spectra_panel(str(spec_h5), str(png), usetex=False)
        used_tex = False
    print(f"\n  wrote {png}  (usetex={used_tex})")

    summary = dict(tokens=tokens, v_sys=v_sys, sxiv_present=bool(has_sxiv),
                   sxiv_column=NS, usetex=used_tex,
                   diag={k: list(v) for k, v in diag.items()},
                   elapsed_s=time.time() - t0)
    (OUT / "smokeA_summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print(f"\n=== SMOKE A done in {time.time()-t0:.0f}s ===")

if __name__ == "__main__":
    main()
