"""Precompute one orientation's LEFT-panel data -> NPZ cache.

Four off-axis scalar maps (display top-down row order) + photometric g/r/i stellar image:
  gas_log_yx        log10 Sigma_gas [Msun/kpc^2]   (column, weight=None)
  temperature_log_yx log10 T [K]                   (density-weighted)
  hi_log_yx         log10 N_HI [cm^-2]             (column, weight=None)
  vlos_yx           rest-frame v_LOS [km/s]        (density-weighted, v_sys subtracted)
  stellar_rgb_yx    photometric g/r/i mock RGB     (common.photometric_stellar_rgb)

Usage: python precompute_projection.py <segment> <inc_deg> <alpha_deg> <out_npz>
"""
from __future__ import annotations
import os, sys, time
from pathlib import Path
import numpy as np
import h5py

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, os.environ.get("CGM_ORIENT_DIR", ""))  # orient_m61, pm_general
sys.path.insert(0, os.environ.get("CGM_STYLE_DIR", ""))  # common.py
import movie_config as C
import movie_geom as G


def _to_display(image):
    """yt off_axis returns [i_col=x(east), i_row=y(north)]; convert to display
    top-down (row0=top=north+, col0=left=east-)."""
    return np.ascontiguousarray(np.asarray(image).T[::-1])


def add_vlos_rest_field(ds, los, v_sys):
    import yt
    lx, ly, lz = float(los[0]), float(los[1]), float(los[2]); vs = float(v_sys)
    def _vlos_rest(field, data):
        vx = data[("gas", "velocity_x")].to("km/s").value
        vy = data[("gas", "velocity_y")].to("km/s").value
        vz = data[("gas", "velocity_z")].to("km/s").value
        return (vx * lx + vy * ly + vz * lz - vs) * yt.units.km / yt.units.s
    ds.add_field(("gas", "vlos_rest"), function=_vlos_rest, units="km/s",
                 sampling_type="local", force_override=True)


def off_axis(ds, los, north, field, weight):
    import yt
    center = ds.arr(C.CENTER_CKPCH.tolist(), "code_length")
    width = ds.arr([2 * C.HALF_WIDTH_KPC, 2 * C.HALF_WIDTH_KPC], "kpc")
    kw = dict(center=center, normal_vector=los.tolist(), width=width,
              resolution=(C.NPIX, C.NPIX), item=field, weight=weight,
              north_vector=north.tolist())
    try:
        img = yt.off_axis_projection(ds, depth=ds.quan(2 * C.DEPTH_KPC, "kpc"), **kw)
    except TypeError:
        img = yt.off_axis_projection(ds, **kw)   # older yt without depth kwarg
    return img


def stellar_photometric_rgb(ds, vb, chunk=400000):
    """Rotate stars into image plane, build g/r/i luminosity mock (display order)."""
    import common
    east = vb["east"]; north = vb["north"]; los = vb["los"]
    xs = []; ys = []; lg = []; lr = []; li = []
    with h5py.File(C.CUTOUT, "r") as f:
        st = f["PartType4"]; n = st["Coordinates"].shape[0]
        has_phot = "GFM_StellarPhotometrics" in st
        for s0 in range(0, n, chunk):
            s1 = min(s0 + chunk, n)
            coords = st["Coordinates"][s0:s1].astype(float)
            rel = coords / C.TNG_H - C.CENTER_KPC[None, :]
            x_img = rel @ east; y_img = rel @ north; z_los = rel @ los
            form = st["GFM_StellarFormationTime"][s0:s1].astype(float)
            keep = (form > 0) & (np.abs(x_img) < C.HALF_WIDTH_KPC) & \
                   (np.abs(y_img) < C.HALF_WIDTH_KPC) & (np.abs(z_los) < 2 * C.DEPTH_KPC)
            if not keep.any():
                continue
            if has_phot:
                phot = st["GFM_StellarPhotometrics"][s0:s1].astype(float)  # U,B,V,K,g,r,i,z
                g_mag = phot[:, 4][keep]; r_mag = phot[:, 5][keep]; i_mag = phot[:, 6][keep]
                lg.append(10 ** (-0.4 * g_mag)); lr.append(10 ** (-0.4 * r_mag))
                li.append(10 ** (-0.4 * i_mag))
            else:  # fallback: mass-light
                m = st["Masses"][s0:s1].astype(float)[keep]
                lg.append(m); lr.append(m); li.append(m)
            xs.append(x_img[keep]); ys.append(y_img[keep])
    x = np.concatenate(xs); y = np.concatenate(ys)
    lg = np.concatenate(lg); lr = np.concatenate(lr); li = np.concatenate(li)
    return colorful_stellar_rgb(x, y, lg, lr, li, half_width_kpc=C.HALF_WIDTH_KPC, npix=1200)


def colorful_stellar_rgb(x, y, lum_g, lum_r, lum_i, half_width_kpc, npix=1200,
                         Q=8.0, alpha=0.85, sat=1.45):
    """Beautiful SDSS g/r/i composite via the Lupton et al. (2004) asinh algorithm:
    RGB=(i,r,g). The asinh stretch reveals the faint extended disk while preserving the true
    band colours (blue young disk, red/yellow old bulge); a mild saturation boost makes it
    pop. Returns display-order (row0=top) RGB."""
    from scipy.ndimage import gaussian_filter
    hw = half_width_kpc
    bins = [np.linspace(-hw, hw, npix + 1)] * 2
    sel = (np.abs(x) < hw) & (np.abs(y) < hw)
    def H(l):
        h, _, _ = np.histogram2d(y[sel], x[sel], bins=bins, weights=l[sel])
        return gaussian_filter(h, 1.0)
    R, Gc, B = H(lum_i), H(lum_r), H(lum_g)          # R=i (reddest), G=r, B=g (bluest)
    bright = R + Gc + B; pos = bright > 0
    # reference scale: a mid-high percentile so the bulge ~ saturates and the disk shows colour
    sb = (np.nanpercentile(bright[pos], 98.5) if pos.any() else 1.0) or 1.0
    r, g, b = R / sb, Gc / sb, B / sb
    I = (r + g + b) / 3.0 + 1e-12
    val = np.arcsinh(alpha * Q * I) / Q              # Lupton asinh stretch
    rgb = np.stack([r, g, b], axis=-1) * (val / I)[..., None]
    # clip preserving hue (rescale over-bright pixels by their max channel)
    mx = np.maximum.reduce([rgb[..., 0], rgb[..., 1], rgb[..., 2]])
    rgb = rgb / np.maximum(mx, 1.0)[..., None]
    # mild saturation boost
    lum = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2])[..., None]
    rgb = np.clip(lum + sat * (rgb - lum), 0.0, 1.0)
    return np.ascontiguousarray(rgb[::-1]).astype(np.float32)         # display: row0=top


def main():
    seg = sys.argv[1]; inc = float(sys.argv[2]); alpha = float(sys.argv[3]); out_npz = sys.argv[4]
    if Path(out_npz).exists():
        try:
            np.load(out_npz)  # corrupt-cache guard
            print(f"[skip] {out_npz} exists"); return
        except Exception:
            print(f"[recompute] corrupt {out_npz}")
    t0 = time.time()
    import yt, trident
    yt.set_log_level(40)
    vb = G.view_basis(inc, alpha, mode=C.MODE)
    los, north, v_sys = vb["los"], vb["north"], vb["v_sys"]
    print(f"seg={seg} inc={inc} alpha={alpha} v_sys={v_sys:+.2f}  loading cutout...")
    ds = yt.load(C.CUTOUT)
    trident.add_ion_fields(ds, ions=["H I"], ftype="gas")
    add_vlos_rest_field(ds, los, v_sys)

    print(f"  projecting (t={time.time()-t0:.0f}s)...")
    sigma = off_axis(ds, los, north, ("gas", "density"), None)               # column g/cm^2
    sigma_msun_kpc2 = np.asarray(sigma.to("g/cm**2")) * (C.CM_PER_KPC ** 2 / C.MSUN_G)
    temp = np.asarray(off_axis(ds, los, north, ("gas", "temperature"), ("gas", "density")))
    nhi = off_axis(ds, los, north, ("gas", "H_p0_number_density"), None)
    try:
        nhi_cm2 = np.asarray(nhi.to("cm**-2"))
    except Exception:
        nhi_cm2 = np.asarray(nhi) * C.CM_PER_KPC
    vlos = np.asarray(off_axis(ds, los, north, ("gas", "vlos_rest"), ("gas", "density")))

    with np.errstate(divide="ignore", invalid="ignore"):
        gas_log = _to_display(np.log10(sigma_msun_kpc2))
        temp_log = _to_display(np.log10(temp))
        hi_log = _to_display(np.log10(nhi_cm2))
        vlos_yx = _to_display(vlos)

    print(f"  stellar g/r/i mock (t={time.time()-t0:.0f}s)...")
    stellar_rgb = stellar_photometric_rgb(ds, vb)

    Path(out_npz).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_npz,
                        gas_log_yx=gas_log.astype("float32"),
                        temperature_log_yx=temp_log.astype("float32"),
                        hi_log_yx=hi_log.astype("float32"),
                        vlos_yx=vlos_yx.astype("float32"),
                        stellar_rgb_yx=stellar_rgb.astype("float32"),
                        los=los, north=north, east=vb["east"], v_sys=v_sys,
                        inc=inc, alpha=alpha, mode=C.MODE,
                        half_width_kpc=C.HALF_WIDTH_KPC, depth_kpc=C.DEPTH_KPC,
                        center_kpc=C.CENTER_KPC)
    # sanity
    finite = np.isfinite(hi_log)
    print(f"  N_HI log range [{np.nanmin(hi_log[finite]):.1f},{np.nanmax(hi_log[finite]):.1f}] "
          f"(face-on disk should peak ~20-21)")
    print(f"  v_LOS range [{np.nanmin(vlos_yx):.0f},{np.nanmax(vlos_yx):.0f}] km/s")
    print(f"[done] {out_npz}  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
