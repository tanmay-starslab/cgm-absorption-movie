"""Central configuration for the CGM absorption-spectroscopy movie.

Everything machine- or galaxy-specific is collected here so the whole pipeline (manifest,
projections, spectra, frame assembly) stays consistent. Paths are read from environment
variables (``CGM_*``) with safe fallbacks, so the repository contains no absolute paths.

Quick start
-----------
1. Provide the two helper-module directories and a python with ``yt`` + ``trident``::

       export CGM_ORIENT_DIR=/path/to/orientation_helpers   # orient_m61.py, pm_general.py
       export CGM_STYLE_DIR=/path/to/styling_helpers        # common.py
       export CGM_PYTHON=/path/to/python                     # yt + trident installed

2. Point at your snapshot/cutout and a (large) output directory::

       export CGM_CUTOUT=/path/to/snapshot_or_cutout.hdf5
       export CGM_DATA_ROOT=/path/to/scratch/cgm_movie

3. Edit the GALAXY block below for your target (centre, virial radius, disk normal,
   systemic velocity, observed inclination, sightline azimuth).

The values committed here are a working EXAMPLE: TNG50-1 subhalo 488530 at z=0.
"""
from __future__ import annotations
import os
import numpy as np
from pathlib import Path

# ── Repository root (auto-derived; never hard-coded) ───────────────────────────
REPO_ROOT = Path(os.environ.get("CGM_REPO", Path(__file__).resolve().parent.parent))

# ── External helper modules (required dependencies; set via env) ───────────────
# Directory holding the orientation helpers (orient_m61.py, pm_general.py):
ORIENT_DIR = os.environ.get("CGM_ORIENT_DIR", "")
# Directory holding the styling/compositing helper (common.py):
STYLE_DIR  = os.environ.get("CGM_STYLE_DIR", "")
# Python interpreter with yt + trident installed (used by the Slurm scripts):
PYTHON     = os.environ.get("CGM_PYTHON", "python")
# Trident line list (only needed if you validate line tokens against the raw file):
LINE_LIST  = os.environ.get("CGM_LINE_LIST", "")

# ── Galaxy / snapshot — EDIT THIS BLOCK FOR YOUR TARGET ────────────────────────
# Example target: TNG50-1 subhalo 488530, snapshot 99 (z=0).
SID        = int(os.environ.get("CGM_SID", 488530))      # subhalo / object id (labelling only)
SNAP       = 99
CUTOUT     = os.environ.get("CGM_CUTOUT", "")            # snapshot or cutout file (yt-loadable)
SIM_H      = float(os.environ.get("CGM_HUBBLE", 0.6774)) # little-h (code-length <-> physical kpc)
SIM_NAME   = os.environ.get("CGM_SIM_NAME", "TNG50-1")
Z_REDSHIFT = 0.0
CENTER_KPC = np.array([41686.43, 29121.38, 6969.31])     # galaxy centre, physical kpc
RVIR_KPC   = 457.0                                       # virial radius, physical kpc
# Disk normal (unit vector in the simulation box frame) — defines face-on:
DISK_NORMAL = np.array([0.11920853967560568, -0.8396884686148283, -0.5298231778090631])
SUBHALO_VEL = np.array([85.6135, -84.1245, 44.9702])     # systemic velocity, km/s (subtracted)
OBS_INC_DEG = 23.0                                       # observed inclination
QSO_PHI_DEG = -157.32742842505516                        # sky azimuth of the sightline
MODE        = "noflip"                                   # fixed for the whole movie

CENTER_CKPCH = CENTER_KPC * SIM_H                         # code length (ckpc/h)
TNG_H        = SIM_H                                      # backward-compatible alias

# ── Output locations (heavy data lives outside the repo) ───────────────────────
DATA_ROOT  = Path(os.environ.get("CGM_DATA_ROOT", REPO_ROOT / "data"))
PROJ_DIR   = DATA_ROOT / "projections"
SPEC_DIR   = DATA_ROOT / "spectra"
RAY_DIR    = DATA_ROOT / "rays"
FRAME_DIR  = DATA_ROOT / "frames"
RESULTS    = REPO_ROOT / "results"


def ensure_paths():
    """Insert the external helper-module directories onto sys.path (idempotent)."""
    import sys
    for p in (ORIENT_DIR, STYLE_DIR):
        if p and p not in sys.path:
            sys.path.insert(0, p)


# ── Projection (LEFT panel) parameters ─────────────────────────────────────────
HALF_WIDTH_KPC = 200.0          # half-size of the (square) field of view in kpc
DEPTH_KPC      = 150.0          # +/- LOS integration depth in kpc
NPIX           = 1536           # projection map resolution
CM_PER_KPC     = 3.0856775814913673e21
MSUN_G         = 1.98847e33
FRAME_DPI      = 160            # output frame DPI (downscaled at encode -> crisp)

# Stellar photometric inset (ellipse): fixed semi-major; minor floored so edge-on stays visible
STELLAR_A_KPC     = 30.0        # semi-major (fixed)
STELLAR_B_MIN_KPC = 9.0         # minor-axis floor (edge-on disk height)

# FIXED colormap limits across ALL frames (visual continuity) — never auto-scale.
GAS_LIMITS  = (4.5, 8.0)        # log10 Msun/kpc^2
TEMP_LIMITS = (4.0, 6.5)        # log10 K
VLOS_LIMITS = (-200.0, 200.0)   # km/s (rest-frame)
HI_LIMITS   = (13.0, 23.0)      # log10 cm^-2
HI_CMAP     = "turbo"           # base name (frame assembly uses a custom high-contrast map)
HI_GAMMA    = 0.60              # stretch -> more contrast at the ends
HI_TICKS    = [13, 15, 17, 19, 21, 23]

# ── Ion set (RIGHT panel), ordered low->high ionization potential ──────────────
# trident's line token is "<Elem> <Ion> <ROUND(wavelength)>" (rounded, not truncated);
# e.g. 1215.67 -> 1216, 1334.53 -> 1335, 417.66 -> 418. Tokens are validated (single clean
# line per token, fresh LineDatabase) in smoke test A.
IONS = [
    dict(key="H_I_1216",    label=r"H\,\textsc{i}\,$\lambda$1216",      rest_A=1215.6701, ion="H I",
         field="H_p0_number_density",  tokens=["H I 1216"]),
    dict(key="Mg_II_2796",  label=r"Mg\,\textsc{ii}\,$\lambda$2796",    rest_A=2796.3520, ion="Mg II",
         field="Mg_p1_number_density", tokens=["Mg II 2796"]),
    dict(key="Si_II_1260",  label=r"Si\,\textsc{ii}\,$\lambda$1260",    rest_A=1260.4221, ion="Si II",
         field="Si_p1_number_density", tokens=["Si II 1260"]),
    dict(key="C_II_1335",   label=r"C\,\textsc{ii}\,$\lambda$1335",     rest_A=1334.5323, ion="C II",
         field="C_p1_number_density",  tokens=["C II 1335"]),
    dict(key="Si_IV_1403",  label=r"Si\,\textsc{iv}\,$\lambda$1403",    rest_A=1402.7700, ion="Si IV",
         field="Si_p3_number_density", tokens=["Si IV 1403"]),
    dict(key="C_IV_1548",   label=r"C\,\textsc{iv}\,$\lambda$1548",     rest_A=1548.1870, ion="C IV",
         field="C_p3_number_density",  tokens=["C IV 1548"]),
    dict(key="N_V_1239",    label=r"N\,\textsc{v}\,$\lambda$1239",      rest_A=1238.8210, ion="N V",
         field="N_p4_number_density",  tokens=["N V 1239"]),
    dict(key="O_VI_1032",   label=r"O\,\textsc{vi}\,$\lambda$1032",     rest_A=1031.9120, ion="O VI",
         field="O_p5_number_density",  tokens=["O VI 1032"]),
    dict(key="Ne_VIII_770", label=r"Ne\,\textsc{viii}\,$\lambda$770",   rest_A=770.4090,  ion="Ne VIII",
         field="Ne_p7_number_density", tokens=["Ne VIII 770"]),
    dict(key="S_XIV_418",   label=r"S\,\textsc{xiv}\,$\lambda$418",     rest_A=417.6600,  ion="S XIV",
         field="S_p13_number_density", tokens=["S XIV 418"]),
]
SPECTRA_ION_LIST = [d["ion"] for d in IONS]   # for trident.add_ion_fields
VEL_WINDOW_KMS   = 1000.0                      # display window +/- (km/s)
VEL_PAD_KMS      = 1300.0                      # generator window +/- (km/s)
SPECTRA_CMAP     = "turbo"                     # sequential, non-white-middle (low->high IP)
DV_KMS           = 2.0                         # velocity sampling
C_KMS            = 299792.458

# ── Animation (3 segments) ─────────────────────────────────────────────────────
# A dense keyframe grid (expensive precompute) is decoupled from the render frames
# (cheap; each snaps to the nearest keyframe and draws the continuously-moving marker).
FPS_TARGET   = 30
DURATION_S   = 75.0
N_FRAMES = dict(seg1=550, seg2=550, seg3=550)   # render frames per segment (1650 total)
N_KEY    = dict(seg1=160, seg2=120, seg3=180)   # keyframe (precompute) samples per segment

SEG1 = dict(inc_deg=OBS_INC_DEG, alpha_deg=0.0, rho_start=150.0, rho_end=2.0)  # sweep rho
SEG2 = dict(rho_kpc=30.0, alpha_deg=0.0, inc_path=[23.0, 90.0, 0.0, 23.0])     # sweep inclination
SEG3 = dict(rho_kpc=30.0, inc_deg=23.0, alpha_start=0.0, alpha_end=360.0)      # sweep azimuth

# Optional figure headline (frame assembly draws no headline by default).
HEADLINE = os.environ.get(
    "CGM_HEADLINE",
    r"Probing the multiphase CGM with background-QSO absorption")
