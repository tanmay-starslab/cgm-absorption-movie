"""Central configuration for the CGM absorption movie (TNG50 sub 488530).

All physical constants, paths, ion set, colormap limits, and the 3-segment animation
parameters live here so every stage (manifest, projections, spectra, frames) is consistent.
"""
from __future__ import annotations
import numpy as np
from pathlib import Path

# ── External code to reuse (added to sys.path by each script) ──────────────────
M61_SCRIPTS  = "/scratch/tsingh65/m61-tng/scripts"
FINESST_FIG2 = "/home/tsingh65/finesst-codes/code/figure2"
TRIDENT_PY   = "/home/tsingh65/.conda/envs/trident/bin/python"
LINE_LIST    = "/home/tsingh65/src/trident/trident/data/line_lists/lines.txt"

# ── Galaxy / cutout (verified, do not re-derive) ───────────────────────────────
SID        = 488530
SNAP       = 99
CUTOUT     = "/data/sborthak/m61/cutouts/out_sub_488530/cutout_ALLFIELDS_sphere_2p1Rvir_sub488530.hdf5"
TNG_H      = 0.6774
CENTER_KPC = np.array([41686.43, 29121.38, 6969.31])      # physical kpc
CENTER_CKPCH = CENTER_KPC * TNG_H                          # code length (ckpc/h)
RVIR_KPC   = 457.0
DISK_NORMAL = np.array([0.11920853967560568, -0.8396884686148283, -0.5298231778090631])
SUBHALO_VEL = np.array([85.6135, -84.1245, 44.9702])      # km/s (systemic)
OBS_INC_DEG = 23.0
QSO_PHI_DEG = -157.32742842505516                          # sky azimuth of the sightline
MODE        = "noflip"                                     # fixed for the whole movie
Z_REDSHIFT  = 0.0
SIM_NAME    = "TNG50-1"

# ── Output locations ───────────────────────────────────────────────────────────
DATA_ROOT  = Path("/data/sborthak/m61/edinburgh_movie")
REPO_ROOT  = Path("/home/tsingh65/cgm-absorption-movie")
PROJ_DIR   = DATA_ROOT / "projections"
SPEC_DIR   = DATA_ROOT / "spectra"
RAY_DIR    = DATA_ROOT / "rays"
FRAME_DIR  = DATA_ROOT / "frames"
RESULTS    = REPO_ROOT / "results"

# ── Projection (LEFT panel) parameters ─────────────────────────────────────────
HALF_WIDTH_KPC = 200.0          # 400 kpc box (2x larger; rho<=150 kpc visible)
DEPTH_KPC      = 150.0          # +/-150 kpc LOS depth
NPIX           = 1536           # high-dpi projection maps
CM_PER_KPC     = 3.0856775814913673e21
MSUN_G         = 1.98847e33
FRAME_DPI      = 160            # 2560x1440 frames (downscaled at encode -> crisp)

# Stellar photometric inset (ellipse): fixed semi-major; minor floored so edge-on stays visible
STELLAR_A_KPC     = 30.0        # semi-major (fixed)
STELLAR_B_MIN_KPC = 9.0         # minor-axis floor (edge-on disk height ~7-10 kpc)

# FIXED colormap limits across ALL frames (visual continuity) — never auto-scale.
GAS_LIMITS  = (4.5, 8.0)        # log10 Msun/kpc^2
TEMP_LIMITS = (4.0, 6.5)        # log10 K
VLOS_LIMITS = (-200.0, 200.0)   # km/s (rest-frame)
HI_LIMITS   = (13.0, 23.0)      # log10 cm^-2  (vmin 13, vmax 23)
HI_CMAP     = "turbo"           # high-contrast N_HI map (replaces the low-contrast pink)
HI_GAMMA    = 0.60              # stronger stretch -> more contrast at the ends
HI_TICKS    = [13, 15, 17, 19, 21, 23]

# ── Ion set (RIGHT panel), ordered low->high ionization potential (red->blue) ──
# token candidates are validated in smoke A against trident LineDatabase.parse_subset.
# NOTE: trident's line token is "<Elem> <Ion> <ROUND(wavelength)>" (rounded, not truncated).
# e.g. 1215.67 -> 1216, 1334.53 -> 1335, 417.66 -> 418. Tokens below use the rounded value
# (validated single-clean-line in smoke A with a FRESH LineDatabase per token).
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
VEL_WINDOW_KMS   = 1000.0                      # display window +/- (-1000..1000)
VEL_PAD_KMS      = 1300.0                      # generator window +/-
SPECTRA_CMAP     = "turbo"                     # sequential, non-white-middle (low->high IP)
DV_KMS           = 2.0                         # velocity sampling
C_KMS            = 299792.458

# ── Animation (3 segments) ─────────────────────────────────────────────────────
# Keyframe grid (expensive precompute) vs render frames (cheap, snap to nearest keyframe).
FPS_TARGET   = 30
DURATION_S   = 75.0
# render frames per segment (dense; ~equal time per segment)
N_FRAMES = dict(seg1=550, seg2=550, seg3=550)   # 1650 total (user: 1500-1800)
# keyframe (precompute) grid sizes per segment.
# seg1 needs only 1 projection (shared) but N spectra (rho varies);
# seg2/seg3 need 1 projection + 1 spectra per keyframe.
N_KEY = dict(seg1=160, seg2=120, seg3=180)      # rho / inc / alpha samples

SEG1 = dict(inc_deg=OBS_INC_DEG, alpha_deg=0.0, rho_start=150.0, rho_end=2.0)  # log-eased
SEG2 = dict(rho_kpc=30.0, alpha_deg=0.0, inc_path=[23.0, 90.0, 0.0, 23.0])     # cover edge<->face
SEG3 = dict(rho_kpc=30.0, inc_deg=23.0, alpha_start=0.0, alpha_end=360.0)

HEADLINE = r"Probing the multiphase CGM with background-QSO absorption \textemdash\ TNG50 sub 488530"
