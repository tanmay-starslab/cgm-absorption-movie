"""Enumerate keyframes (expensive precompute grid) and render-frames for the 3 segments.

Writes:
  manifest_proj.csv   unique projection orientations (seg, idx, inc, alpha, npz)
  manifest_spec.csv   unique spectra sightlines      (seg, idx, rho, inc, alpha, h5)
  manifest_frames.csv render frames (seg, frame_idx, global_idx, rho, inc, alpha, proj_npz,
                      spec_h5, frame_png)  -- each snaps to the nearest keyframe.

Usage: python build_manifest.py [outdir]   (default: repo root)
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import movie_config as C


def smoothstep(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def seg1_params(t):  # vary rho 100->2 (log-eased), inc/alpha fixed
    s = smoothstep(t)
    rho = float(np.exp(np.log(C.SEG1["rho_start"]) * (1 - s) + np.log(C.SEG1["rho_end"]) * s))
    return rho, C.SEG1["inc_deg"], C.SEG1["alpha_deg"]


def seg2_params(t):  # vary inc along a multi-leg path, rho/alpha fixed
    path = C.SEG2["inc_path"]; nseg = len(path) - 1
    x = np.clip(t, 0, 1) * nseg
    i = min(int(x), nseg - 1); f = smoothstep(x - i)
    inc = float(path[i] * (1 - f) + path[i + 1] * f)
    return C.SEG2["rho_kpc"], inc, C.SEG2["alpha_deg"]


def seg3_params(t):  # vary alpha 0->360 (linear), rho/inc fixed
    alpha = float(C.SEG3["alpha_start"] * (1 - t) + C.SEG3["alpha_end"] * t)
    return C.SEG3["rho_kpc"], C.SEG3["inc_deg"], alpha


SEGFN = {"seg1": seg1_params, "seg2": seg2_params, "seg3": seg3_params}


def build(outdir=None):
    outdir = Path(outdir) if outdir else C.REPO_ROOT
    proj_rows, spec_rows, frame_rows = [], [], []
    proj_key = {}; spec_key = {}
    gidx = 0
    for seg in ["seg1", "seg2", "seg3"]:
        fn = SEGFN[seg]
        nkey = C.N_KEY[seg]; nframe = C.N_FRAMES[seg]
        # keyframe grid (uniform in t)
        key_t = np.linspace(0, 1, nkey)
        key_params = [fn(t) for t in key_t]
        # unique projection orientations (round inc,alpha) and unique spectra (round rho,inc,alpha)
        for (rho, inc, alpha) in key_params:
            pk = (round(inc, 2), round(alpha, 2))
            if (seg, pk) not in proj_key:
                pidx = len([k for k in proj_key if k[0] == seg])
                npz = str(C.PROJ_DIR / seg / f"proj_{pidx:04d}_inc{inc:06.2f}_a{alpha:06.2f}.npz")
                proj_key[(seg, pk)] = npz
                proj_rows.append(dict(segment=seg, idx=pidx, inc_deg=inc, alpha_deg=alpha, npz=npz))
            sk = (round(rho, 3), round(inc, 2), round(alpha, 2))
            if (seg, sk) not in spec_key:
                sidx = len([k for k in spec_key if k[0] == seg])
                h5 = str(C.SPEC_DIR / seg / f"spec_{sidx:04d}_r{rho:06.2f}_i{inc:06.2f}_a{alpha:06.2f}.h5")
                spec_key[(seg, sk)] = h5
                spec_rows.append(dict(segment=seg, idx=sidx, rho_kpc=rho, inc_deg=inc,
                                      alpha_deg=alpha, h5=h5))
        # keyframe arrays for nearest lookup
        key_arr = np.array(key_params)  # (nkey, 3) rho,inc,alpha
        # render frames
        for fi in range(nframe):
            t = fi / (nframe - 1)
            rho, inc, alpha = fn(t)
            # nearest keyframe by the swept parameter (use full 3-vec distance, scaled)
            d = ((key_arr[:, 0] - rho) / max(1e-6, key_arr[:, 0].ptp() or 1)) ** 2 \
                + ((key_arr[:, 1] - inc) / max(1e-6, key_arr[:, 1].ptp() or 1)) ** 2 \
                + ((key_arr[:, 2] - alpha) / max(1e-6, key_arr[:, 2].ptp() or 1)) ** 2
            kk = int(np.argmin(d))
            krho, kinc, kalpha = key_params[kk]
            proj_npz = proj_key[(seg, (round(kinc, 2), round(kalpha, 2)))]
            spec_h5 = spec_key[(seg, (round(krho, 3), round(kinc, 2), round(kalpha, 2)))]
            png = str(C.FRAME_DIR / seg / f"frame_{gidx:05d}.png")
            frame_rows.append(dict(segment=seg, frame_idx=fi, global_idx=gidx,
                                   rho_kpc=rho, inc_deg=inc, alpha_deg=alpha,
                                   proj_npz=proj_npz, spec_h5=spec_h5, frame_png=png))
            gidx += 1
    pd.DataFrame(proj_rows).to_csv(outdir / "manifest_proj.csv", index=False)
    pd.DataFrame(spec_rows).to_csv(outdir / "manifest_spec.csv", index=False)
    pd.DataFrame(frame_rows).to_csv(outdir / "manifest_frames.csv", index=False)
    print(f"manifest: {len(proj_rows)} projections, {len(spec_rows)} spectra, {len(frame_rows)} frames")
    for seg in ["seg1", "seg2", "seg3"]:
        np_ = len([r for r in proj_rows if r['segment'] == seg])
        ns_ = len([r for r in spec_rows if r['segment'] == seg])
        print(f"  {seg}: {np_} proj, {ns_} spec, {C.N_FRAMES[seg]} frames")
    return outdir


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else None)
