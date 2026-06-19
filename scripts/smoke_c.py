"""SMOKE TEST C — 3 frames per segment (start/mid/end) to verify continuity & motion.
Loads the cutout ONCE, computes the needed projections + spectra, assembles 9 frames, and
builds a 3x3 contact sheet. Seg1 reuses one projection (rho varies); seg2/seg3 vary orientation.
"""
from __future__ import annotations
import sys, time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, "/scratch/tsingh65/m61-tng/scripts")
sys.path.insert(0, "/home/tsingh65/finesst-codes/code/figure2")
import movie_config as C
import movie_geom as G
import movie_spectra as S
import precompute_projection as P
import assemble_frame as AF

OUT = C.RESULTS / "smoke"; OUT.mkdir(parents=True, exist_ok=True)
PROJD = OUT / "c_proj"; SPECD = OUT / "c_spec"; FRD = OUT / "c_frames"
for d in (PROJD, SPECD, FRD): d.mkdir(exist_ok=True)

# 3 frames per segment: (label, rho, inc, alpha)
FRAMES = {
    "seg1": [("start", 100.0, 23.0, 0.0), ("mid", 14.0, 23.0, 0.0), ("end", 2.0, 23.0, 0.0)],
    "seg2": [("start", 30.0, 23.0, 0.0), ("mid", 30.0, 90.0, 0.0), ("end", 30.0, 0.0, 0.0)],
    "seg3": [("start", 30.0, 23.0, 0.0), ("mid", 30.0, 23.0, 180.0), ("end", 30.0, 23.0, 359.0)],
}


def main():
    t0 = time.time()
    import yt, trident
    yt.set_log_level(40)
    tokens = S.validate_tokens(verbose=False)
    print(f"Loading cutout + 10 ion fields (t={time.time()-t0:.0f}s)...")
    ds = yt.load(C.CUTOUT)
    trident.add_ion_fields(ds, ions=C.SPECTRA_ION_LIST, ftype="gas")

    proj_cache = {}; spec_cache = {}
    def get_proj(inc, alpha):
        key = (round(inc, 2), round(alpha, 2))
        if key in proj_cache: return proj_cache[key]
        vb = G.view_basis(inc, alpha, mode=C.MODE)
        P.add_vlos_rest_field(ds, vb["los"], vb["v_sys"])
        sigma = P.off_axis(ds, vb["los"], vb["north"], ("gas", "density"), None)
        sig = np.asarray(sigma.to("g/cm**2")) * (C.CM_PER_KPC**2 / C.MSUN_G)
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
        print(f"  proj inc={inc} a={alpha} done (t={time.time()-t0:.0f}s)")
        return str(npz)

    def get_spec(rho, inc, alpha):
        key = (round(rho, 2), round(inc, 2), round(alpha, 2))
        if key in spec_cache: return spec_cache[key]
        vb = G.view_basis(inc, alpha, mode=C.MODE); sl = G.sightline(vb, rho)
        ray_h5 = SPECD / f"ray_r{rho:05.1f}_i{inc:05.1f}_a{alpha:05.1f}.h5"
        S.build_ray(ds, sl["start_ckpch"], sl["end_ckpch"], ray_h5)
        ray_ds = yt.load(str(ray_h5))
        spec_h5 = SPECD / f"spec_r{rho:05.1f}_i{inc:05.1f}_a{alpha:05.1f}.h5"
        S.generate_movie_spectra(ray_ds, vb["v_sys"], spec_h5, tokens,
                                 meta=dict(rho_kpc=rho, inc_deg=inc, alpha_deg=alpha))
        spec_cache[key] = str(spec_h5)
        print(f"  spec rho={rho} inc={inc} a={alpha} done (t={time.time()-t0:.0f}s)")
        return str(spec_h5)

    # assemble the 9 frames
    frame_paths = {}
    for seg, lst in FRAMES.items():
        for label, rho, inc, alpha in lst:
            npz = get_proj(inc, alpha); sp = get_spec(rho, inc, alpha)
            png = FRD / f"{seg}_{label}.png"
            AF.assemble(npz, sp, rho, inc, alpha, str(png))
            frame_paths[(seg, label)] = str(png)
            print(f"  frame {seg}/{label} assembled")

    # 3x3 contact sheet
    fig, axes = plt.subplots(3, 3, figsize=(30, 16))
    for r, seg in enumerate(["seg1", "seg2", "seg3"]):
        for c, label in enumerate(["start", "mid", "end"]):
            ax = axes[r, c]; ax.imshow(mpimg.imread(frame_paths[(seg, label)])); ax.axis("off")
            ax.set_title(f"{seg} {label}", fontsize=14)
    fig.suptitle("Smoke C: 3 frames/segment (rho sweep / inc sweep / alpha sweep)", fontsize=18)
    fig.tight_layout()
    cs = OUT / "smokeC_contact_sheet.png"
    fig.savefig(cs, dpi=90, facecolor="white"); plt.close(fig)
    print(f"\n[done] contact sheet -> {cs}  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
