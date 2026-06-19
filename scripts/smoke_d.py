"""SMOKE TEST D — verify all the requested tweaks. Recompute 3 projections at the new
400 kpc extent + npix 1536, assemble 4 frames (reusing existing smoke-C spectra), and build a
2x2 contact sheet. Tests: larger extent, stellar ellipse (floored minor axis), black-star
sightline (no ring/line), top-left scalebar, two coloured info boxes, turbo spectra colors,
+/-1000 window + line-name labels, N_HI cbar to 22, bigger colorbars, no headline, high dpi.
"""
from __future__ import annotations
import os, sys, time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, os.environ.get("CGM_ORIENT_DIR", ""))  # orient_m61, pm_general
sys.path.insert(0, os.environ.get("CGM_STYLE_DIR", ""))  # common.py
import movie_config as C
import movie_geom as G
import precompute_projection as P
import assemble_frame as AF

OUT = C.RESULTS / "smoke"; OUT.mkdir(parents=True, exist_ok=True)
PROJD = OUT / "d_proj"; FRD = OUT / "d_frames"
for d in (PROJD, FRD): d.mkdir(exist_ok=True)
CSPEC = OUT / "c_spec"   # reuse smoke-C spectra

# 4 frames: (label, rho, inc, alpha, spectra file)
FRAMES = [
    ("seg1_outer_r100", 100.0, 23.0, 0.0, "spec_r100.0_i023.0_a000.0.h5"),
    ("fiducial_r30",     30.0, 23.0, 0.0, "spec_r030.0_i023.0_a000.0.h5"),
    ("edgeon_r30",       30.0, 90.0, 0.0, "spec_r030.0_i090.0_a000.0.h5"),
    ("faceon_r30",       30.0,  0.0, 0.0, "spec_r030.0_i000.0_a000.0.h5"),
]


def main():
    t0 = time.time()
    import yt, trident
    yt.set_log_level(40)
    print(f"Loading cutout (extent={2*C.HALF_WIDTH_KPC} kpc, npix={C.NPIX})...")
    ds = yt.load(C.CUTOUT)
    trident.add_ion_fields(ds, ions=["H I"], ftype="gas")

    proj_cache = {}
    def get_proj(inc, alpha):
        key = (round(inc, 2), round(alpha, 2))
        if key in proj_cache: return proj_cache[key]
        vb = G.view_basis(inc, alpha, mode=C.MODE)
        P.add_vlos_rest_field(ds, vb["los"], vb["v_sys"])
        sig = np.asarray(P.off_axis(ds, vb["los"], vb["north"], ("gas", "density"), None).to("g/cm**2")) \
              * (C.CM_PER_KPC**2 / C.MSUN_G)
        temp = np.asarray(P.off_axis(ds, vb["los"], vb["north"], ("gas", "temperature"), ("gas", "density")))
        nhi = P.off_axis(ds, vb["los"], vb["north"], ("gas", "H_p0_number_density"), None)
        try: nhi_cm2 = np.asarray(nhi.to("cm**-2"))
        except Exception: nhi_cm2 = np.asarray(nhi) * C.CM_PER_KPC
        vlos = np.asarray(P.off_axis(ds, vb["los"], vb["north"], ("gas", "vlos_rest"), ("gas", "density")))
        star = P.stellar_photometric_rgb(ds, vb)
        npz = PROJD / f"proj_i{inc:05.1f}_a{alpha:05.1f}.npz"
        with np.errstate(divide="ignore", invalid="ignore"):
            np.savez_compressed(npz,
                gas_log_yx=P._to_display(np.log10(sig)).astype("float32"),
                temperature_log_yx=P._to_display(np.log10(temp)).astype("float32"),
                hi_log_yx=P._to_display(np.log10(nhi_cm2)).astype("float32"),
                vlos_yx=P._to_display(vlos).astype("float32"),
                stellar_rgb_yx=star.astype("float32"),
                los=vb["los"], north=vb["north"], east=vb["east"], v_sys=vb["v_sys"],
                inc=inc, alpha=alpha)
        proj_cache[key] = str(npz)
        fin = np.isfinite(P._to_display(np.log10(nhi_cm2)))
        print(f"  proj inc={inc} a={alpha} done (t={time.time()-t0:.0f}s)  "
              f"N_HI<= {np.nanmax(np.log10(nhi_cm2)[np.isfinite(np.log10(nhi_cm2))]):.1f}")
        return str(npz)

    paths = {}
    for label, rho, inc, alpha, specf in FRAMES:
        npz = get_proj(inc, alpha)
        sp = CSPEC / specf
        if not sp.exists():
            print(f"  [WARN] missing spectra {sp}; skipping {label}"); continue
        png = FRD / f"{label}.png"
        AF.assemble(npz, str(sp), rho, inc, alpha, str(png))
        paths[label] = str(png)
        print(f"  frame {label} assembled (t={time.time()-t0:.0f}s)")

    # 2x2 contact sheet
    labels = [f[0] for f in FRAMES if f[0] in paths]
    fig, axes = plt.subplots(2, 2, figsize=(34, 19))
    for ax, lab in zip(axes.ravel(), labels):
        ax.imshow(mpimg.imread(paths[lab])); ax.axis("off"); ax.set_title(lab, fontsize=16)
    for ax in axes.ravel()[len(labels):]: ax.axis("off")
    fig.suptitle("Smoke D: new extent / stellar / sightline / scalebar / info boxes / turbo spectra",
                 fontsize=20)
    fig.tight_layout()
    cs = OUT / "smokeD_contact_sheet.png"
    fig.savefig(cs, dpi=80, facecolor="white"); plt.close(fig)
    print(f"\n[done] -> {cs}  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
