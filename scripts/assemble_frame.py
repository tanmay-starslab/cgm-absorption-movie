"""Assemble one 1920x1080 movie frame: LEFT 4-quadrant projection (+ photometric stellar
inset, bold sightline, corner colorbars OUTSIDE the box, info text in the left margin) and
RIGHT 10-ion spectra stack, with a top headline strip.

Usage: python assemble_frame.py <proj_npz> <spectra_h5> <rho_kpc> <inc_deg> <alpha_deg> <out_png>
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.cm import ScalarMappable
import matplotlib.patheffects as pe

# custom high-contrast N_HI colormap (dark navy -> blue -> cyan -> green -> yellow -> orange ->
# red -> pink/white): strong end-to-end contrast, breaks up the flat-pink default.
HI_CMAP_OBJ = LinearSegmentedColormap.from_list("hi_contrast",
    ["#05010f", "#0b1f6b", "#114fb0", "#13a7b0", "#22b34a", "#9fd320",
     "#f0c01e", "#f0721e", "#d61f2f", "#ffe6f0"])

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, "/scratch/tsingh65/m61-tng/scripts")
sys.path.insert(0, "/home/tsingh65/finesst-codes/code/figure2")
import movie_config as C
import movie_geom as G
import common
import render_spectra_panel as RS

# Use the movie's FIXED limits everywhere (override common's HI default)
common.HI_LOG_LIMITS = C.HI_LIMITS
HW = C.HALF_WIDTH_KPC
A_KPC = C.STELLAR_A_KPC          # stellar inset semi-major axis (fixed)
B_MIN = C.STELLAR_B_MIN_KPC      # minor-axis floor (edge-on disk stays visible)

# figure-fraction layout (16:9, NO headline). Square left panel: w = h * 9/16.
BOX       = [0.100, 0.095, 0.450, 0.800]    # left data box [x0,y0,w,h]; 0.80*9/16=0.45 (square)
SPEC_RECT = [0.585, 0.100, 0.400, 0.790]    # right spectra region
CBAR_H    = 0.014
CBAR_GAP  = 0.009                            # bar sits close to the box; labels/ticks extend into the empty margin
CBAR_LABEL_FS = 18
CBAR_TICK_FS  = 15
CBAR_LABELPAD = 9                            # push label clear of the (top/bottom) tick labels
SCALEBAR_KPC  = 25.0

# distinct colors for i / alpha / rho (values bold)
COL_I, COL_A, COL_R = "#1f6fd6", "#1f9e57", "#d6371f"

CBARS = [   # (key, cmap, limits, ticks, label, corner)
    ("gas",  lambda: common.CMAP_GAS,  C.GAS_LIMITS,  [5, 6, 7, 8],
     r"$\log_{10}\,\Sigma_{\rm gas}\,[{\rm M_\odot\,kpc^{-2}}]$", "TL"),
    ("temp", lambda: common.CMAP_TEMP, C.TEMP_LIMITS, [4, 5, 6],
     r"$\log_{10}\,T\,[{\rm K}]$", "TR"),
    ("hi",   lambda: HI_CMAP_OBJ, C.HI_LIMITS, C.HI_TICKS,
     r"$\log_{10}\,N_{\rm HI}\,[{\rm cm^{-2}}]$", "BL"),
    ("vlos", lambda: common.CMAP_VLOS, C.VLOS_LIMITS, [-200, -100, 0, 100, 200],
     r"$v_{\rm LOS}-v_{\rm sys}\,[{\rm km\,s^{-1}}]$", "BR"),
]


def _square_rect(box, fig_w_over_h=16.0 / 9.0):
    """Shrink [x0,y0,w,h] (fig fraction) so the axes is square in display pixels."""
    x0, y0, w, h = box
    w_px = w * fig_w_over_h   # relative pixel width (h in units of height)
    if w_px > h:              # too wide -> shrink width
        new_w = h / fig_w_over_h
        x0 += (w - new_w) / 2.0; w = new_w
    else:                     # too tall -> shrink height
        new_h = w_px
        y0 += (h - new_h) / 2.0; h = new_h
    return [x0, y0, w, h]


def _composite(z):
    """4-quadrant composite (UL gas, UR temp, LL N_HI, LR v_LOS). Mirrors
    common.build_stitched_composite but renders N_HI with the high-contrast turbo map
    (vmin 13, stronger gamma) instead of the low-contrast pink default."""
    gas = common.scalar_to_rgb(z["gas_log_yx"], common.CMAP_GAS, vmin=C.GAS_LIMITS[0],
        vmax=C.GAS_LIMITS[1], gamma=0.62, use_asinh=False, contrast_sigma=5.0,
        contrast_strength=0.34, edge_strength=0.075)
    temp = common.scalar_to_rgb(z["temperature_log_yx"], common.CMAP_TEMP, vmin=C.TEMP_LIMITS[0],
        vmax=C.TEMP_LIMITS[1], gamma=0.82, use_asinh=False, contrast_sigma=3.2,
        contrast_strength=0.38, edge_strength=0.08)
    temp = common.temperature_clump_boost_rgb(z["temperature_log_yx"], temp)
    hi = common.scalar_to_rgb(z["hi_log_yx"], HI_CMAP_OBJ, vmin=C.HI_LIMITS[0],
        vmax=C.HI_LIMITS[1], gamma=C.HI_GAMMA, use_asinh=False, contrast_sigma=2.6,
        contrast_strength=0.44, edge_strength=0.06)
    vmid = 0.5 * (C.VLOS_LIMITS[0] + C.VLOS_LIMITS[1])
    vlos = common.vlos_to_rgb_diverging(z["vlos_yx"], common.CMAP_VLOS, vmin=C.VLOS_LIMITS[0],
        vmax=C.VLOS_LIMITS[1], vcenter=vmid, gamma=1.0, contrast_sigma=3.8,
        contrast_strength=0.42, edge_strength=0.08)
    ny, nx = gas.shape[:2]; my, mx = ny // 2, nx // 2
    comp = np.zeros((ny, nx, 3), dtype=np.float32)
    comp[:my, :mx] = gas[:my, :mx]; comp[:my, mx:] = temp[:my, mx:]
    comp[my:, :mx] = hi[my:, :mx];  comp[my:, mx:] = vlos[my:, mx:]
    return np.clip(comp, 0.0, 1.0).astype(np.float32)


def render_left(fig, npz, rho_kpc, inc_deg, alpha_deg):
    z = np.load(npz)
    comp = _composite(z)
    # photometric stellar inset: fixed semi-major; minor floored so edge-on disk stays visible
    star_rgb = z["stellar_rgb_yx"]   # already a colourful, stretched RGB (pre-stylized in precompute)
    b_kpc = max(B_MIN, A_KPC * float(np.cos(np.deg2rad(inc_deg))))
    inset, alpha = common.make_elliptical_stellar_inset(
        star_rgb, None, a_kpc=A_KPC, b_kpc=b_kpc, angle_deg=0.0, half_width_kpc=HW, stylize=False)
    comp = common.blend_inset(comp, inset, alpha)

    rect = _square_rect(BOX)
    ax = fig.add_axes(rect)
    ax.imshow(comp, origin="upper", extent=[-HW, HW, -HW, HW], interpolation="nearest")
    ax.set_xlim(-HW, HW); ax.set_ylim(-HW, HW); ax.set_aspect("equal"); ax.set_axis_off()

    # sightline: a single black star at the QSO position (no ring, no centre line)
    vb = G.view_basis(inc_deg, alpha_deg, mode=C.MODE)
    mx, my = G.sightline(vb, rho_kpc)["marker_xy_kpc"]
    ax.plot([mx], [my], marker="*", ms=22, mfc="black", mec="white", mew=1.8, zorder=12,
            path_effects=[pe.withStroke(linewidth=1.6, foreground="white")])

    # 25 kpc scale bar at the top-left of the panel
    sbx0 = -0.90 * HW; sby = 0.88 * HW
    ax.plot([sbx0, sbx0 + SCALEBAR_KPC], [sby, sby], color="white", lw=4.0,
            solid_capstyle="butt", zorder=12,
            path_effects=[pe.withStroke(linewidth=6.0, foreground="black")])
    ax.text(sbx0 + SCALEBAR_KPC / 2, sby + 0.025 * HW, rf"{int(SCALEBAR_KPC)}\,kpc",
            color="white", fontsize=15, fontweight="bold", ha="center", va="bottom", zorder=12,
            path_effects=[pe.withStroke(linewidth=2.6, foreground="black")])

    # corner colorbars OUTSIDE the box (tighter gap, bigger labels/ticks)
    bx0, by0, bw, bh = rect
    half = bw / 2.0 - 0.010
    pos = {"TL": [bx0, by0 + bh + CBAR_GAP, half, CBAR_H],
           "TR": [bx0 + bw / 2 + 0.010, by0 + bh + CBAR_GAP, half, CBAR_H],
           "BL": [bx0, by0 - CBAR_GAP - CBAR_H, half, CBAR_H],
           "BR": [bx0 + bw / 2 + 0.010, by0 - CBAR_GAP - CBAR_H, half, CBAR_H]}
    for key, cmap_fn, lim, ticks, label, corner in CBARS:
        cax = fig.add_axes(pos[corner])
        sm = ScalarMappable(norm=Normalize(*lim), cmap=cmap_fn())
        cb = fig.colorbar(sm, cax=cax, orientation="horizontal", ticks=ticks)
        cb.set_label(label, fontsize=CBAR_LABEL_FS, labelpad=CBAR_LABELPAD)
        cax.tick_params(labelsize=CBAR_TICK_FS, length=3, pad=2)
        cax.xaxis.set_ticks_position("top" if corner.startswith("T") else "bottom")
        cax.xaxis.set_label_position("top" if corner.startswith("T") else "bottom")

    # two info boxes in the left margin (kept fully inside the figure; reduced inner padding)
    import matplotlib.patches as mpatches
    cy = by0 + bh * 0.5
    # box 1: simulation / subhalo / redshift (single colour)
    fig.text(0.020, cy + 0.090,
             "\n".join([rf"\textbf{{{C.SIM_NAME}}}", rf"sub\,{C.SID}", rf"$z={C.Z_REDSHIFT:.2f}$"]),
             fontsize=14.5, va="center", ha="left", linespacing=1.5, color="black",
             bbox=dict(boxstyle="round,pad=0.30", fc="white", ec="0.35", lw=1.3))
    # box 2: i / alpha / rho (each its own colour, value bold) -- one box, 3 coloured lines
    bxx, bxy, bxw, bxh = 0.016, cy - 0.150, 0.078, 0.130
    fig.patches.append(mpatches.FancyBboxPatch(
        (bxx, bxy), bxw, bxh, boxstyle="round,pad=0.004",
        transform=fig.transFigure, fc="white", ec="0.35", lw=1.3, zorder=5, clip_on=False))
    lines = [(rf"$i=\mathbf{{{inc_deg:.0f}}}^{{\circ}}$", COL_I),
             (rf"$\alpha=\mathbf{{{alpha_deg:.0f}}}^{{\circ}}$", COL_A),
             (rf"$\rho=\mathbf{{{rho_kpc:.0f}}}\ \mathrm{{kpc}}$", COL_R)]
    for j, (txt, col) in enumerate(lines):
        fig.text(bxx + 0.011, bxy + bxh - 0.028 - j * 0.041, txt, fontsize=16,
                 va="center", ha="left", color=col, zorder=6)
    return ax


def assemble(proj_npz, spectra_h5, rho_kpc, inc_deg, alpha_deg, out_png, usetex=True):
    RS.set_style(usetex)
    fig = plt.figure(figsize=(16.0, 9.0), dpi=C.FRAME_DPI, facecolor="white")  # no headline
    render_left(fig, proj_npz, rho_kpc, inc_deg, alpha_deg)
    # right spectra stack
    outer = gridspec.GridSpec(1, 1, left=SPEC_RECT[0], right=SPEC_RECT[0] + SPEC_RECT[2],
                              bottom=SPEC_RECT[1], top=SPEC_RECT[1] + SPEC_RECT[3])
    RS.render_spectra_axes(fig, outer[0], spectra_h5)
    fig.savefig(out_png, dpi=C.FRAME_DPI, facecolor="white")
    plt.close(fig)
    return out_png


if __name__ == "__main__":
    a = sys.argv
    assemble(a[1], a[2], float(a[3]), float(a[4]), float(a[5]), a[6])
    print("wrote", a[6])
