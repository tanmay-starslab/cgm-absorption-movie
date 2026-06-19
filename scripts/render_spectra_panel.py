"""Render the RIGHT panel: vertical stack of 10 ion absorption spectra (raw flux vs velocity).

Low->high ionization potential top->bottom; thick curves colored red->blue; ion name boxed
bottom-left of each row; shared velocity x-axis; common 'Normalized Flux' y-label; usetex.
Importable (render_spectra_axes for the composite frame) or standalone (render_spectra_panel).
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import gridspec

sys.path.insert(0, str(Path(__file__).parent))
import movie_config as C

# sequential, non-white-middle colormap (low IP -> high IP); sample inside [0.04,0.96] so the
# extreme-dark ends stay visible on a white background.
_CMAP = plt.get_cmap(C.SPECTRA_CMAP)
ION_COLORS = [_CMAP(0.04 + 0.92 * i / (len(C.IONS) - 1)) for i in range(len(C.IONS))]


def set_style(usetex=True):
    plt.rcParams.update({
        "text.usetex": usetex, "font.family": "serif",
        "font.size": 20, "axes.labelsize": 26, "xtick.labelsize": 20,
        "ytick.labelsize": 15, "axes.linewidth": 1.5,
        "mathtext.fontset": "cm",
    })
    if usetex:
        plt.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"


def render_spectra_axes(fig, subspec, spec_h5, vwin=C.VEL_WINDOW_KMS, y_label=True):
    """Render the 10-row stack into a GridSpecFromSubplotSpec inside `subspec`."""
    n = len(C.IONS)
    inner = gridspec.GridSpecFromSubplotSpec(n, 1, subplot_spec=subspec, hspace=0.0)
    axes = [fig.add_subplot(inner[i]) for i in range(n)]
    with h5py.File(spec_h5, "r") as f:
        for i, d in enumerate(C.IONS):
            ax = axes[i]; g = f["by_line"][d["key"]]
            v = g["vel"][()]; fl = g["flux"][()]
            m = (v >= -vwin) & (v <= vwin)
            ax.plot(v[m], fl[m], color=ION_COLORS[i], lw=3.0, solid_capstyle="round", zorder=4)
            ax.axhline(1.0, color="0.55", lw=0.8, ls=":", zorder=1)
            ax.axvline(0.0, color="0.55", lw=0.8, ls=":", zorder=1)
            ax.set_xlim(-vwin, vwin); ax.set_ylim(-0.08, 1.20)
            ax.set_yticks([0.0, 1.0])
            ax.text(0.016, 0.11, d["label"], transform=ax.transAxes, ha="left", va="bottom",
                    fontsize=17, zorder=6,
                    bbox=dict(boxstyle="round,pad=0.22", fc="white", ec=ION_COLORS[i],
                              lw=2.0, alpha=0.94))
            ax.tick_params(direction="in", top=True, right=True, length=6, width=1.2)
            if i != n - 1:
                ax.set_xticklabels([])
    axes[-1].set_xlabel(r"$v_{\mathrm{LOS}}-v_{\mathrm{sys}}\ \ [\mathrm{km\,s^{-1}}]$")
    axes[-1].set_xticks([-1000, -500, 0, 500, 1000])
    if y_label:
        # common y-label centered on the stack (closer to the axis -> less pad)
        x0 = axes[0].get_position().x0
        fig.text(x0 - 0.030, 0.5 * (axes[0].get_position().y1 + axes[-1].get_position().y0),
                 r"Normalized Flux", va="center", rotation="vertical", fontsize=25)
    return axes


def render_spectra_panel(spec_h5, out_png, figsize=(7.2, 11.2), usetex=True):
    set_style(usetex)
    fig = plt.figure(figsize=figsize)
    outer = gridspec.GridSpec(1, 1, left=0.17, right=0.975, top=0.99, bottom=0.065)
    render_spectra_axes(fig, outer[0], spec_h5)
    fig.savefig(out_png, dpi=130, facecolor="white")
    plt.close(fig)
    return out_png


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("spec_h5"); ap.add_argument("out_png")
    ap.add_argument("--no-usetex", action="store_true")
    a = ap.parse_args()
    render_spectra_panel(a.spec_h5, a.out_png, usetex=not a.no_usetex)
    print("wrote", a.out_png)
