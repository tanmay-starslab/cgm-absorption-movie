# CGM Absorption-Spectroscopy Movie

Generate a publication-grade, split-panel animation that shows how a **background-quasar
absorption sightline probes the multiphase circumgalactic medium (CGM)** of a simulated
galaxy. Built on [`yt`](https://yt-project.org) (off-axis projections) and
[`Trident`](https://trident.readthedocs.io) (ion fields + synthetic absorption spectra),
and parallelised with Slurm.

Each frame is a single, continuous figure:

- **Left** — a 4-quadrant off-axis projection of the galaxy + CGM:
  gas surface density Σ<sub>gas</sub>, mass-weighted temperature *T*, rest-frame
  line-of-sight velocity *v*<sub>LOS</sub>, and neutral-hydrogen column *N*<sub>HI</sub>,
  with a photometric *g/r/i* stellar-centre inset, a bold sightline marker, and a scalebar.
- **Right** — a vertical stack of **10 ion absorption spectra** (raw flux vs. velocity),
  ordered low → high ionization potential (H I → S XIV), each a single clean transition.

The animation has three continuous segments that sweep the three observational degrees of
freedom of a QSO–galaxy absorption experiment:

| Segment | Fixed | Swept | What it shows |
|--------|-------|-------|---------------|
| 1 | inclination, azimuth | **impact parameter ρ** | sightline moving from the outer CGM into the inner disk |
| 2 | ρ, azimuth | **inclination** | galaxy turning edge-on ↔ face-on |
| 3 | ρ, inclination | **azimuth α** (0–360°) | galaxy spinning about its disk normal (observer fixed) |

An example render (`results/cgm_movie_50fps.mp4`) is included — the example target is
**TNG50-1 subhalo 488530** at *z* = 0, but the pipeline runs on any galaxy in a cosmological
hydrodynamic snapshot that `yt` + `Trident` can load (IllustrisTNG, SIMBA, FIRE, EAGLE, …).

## How it works

A dense **keyframe grid** (the expensive precompute: off-axis maps + Trident rays/spectra)
is decoupled from the **render frames** (cheap matplotlib compositing). Each render frame
snaps to its nearest keyframe and draws the continuously-moving sightline marker, so motion
stays smooth without recomputing physics every frame. Velocities use
`use_doppler_redshift_only=True` and the galaxy's **systemic velocity is subtracted** from
both the projection maps and the spectra, so the velocity axes are consistent.

## Requirements

- Python 3.9+ with **`yt`**, **`Trident`**, `numpy`, `scipy`, `pandas`, `h5py`, `matplotlib`.
- A **LaTeX** install (`latex` + `dvipng`) — figures use `text.usetex=True`.
- **ffmpeg** (with libx264) for encoding.
- A scheduler — examples use **Slurm** (the scripts also run standalone).
- Two small **external helper modules** you point at via environment variables:
  - **orientation helpers** — `orient_m61.py`, `pm_general.py`
    (build the view basis and sightline geometry); directory set by `CGM_ORIENT_DIR`.
  - **styling helper** — `common.py` (compositing, colorbars, stellar inset);
    directory set by `CGM_STYLE_DIR`.

## Configuration

Everything machine- and galaxy-specific is read from environment variables (no absolute
paths live in the repo). Set them in your shell, or copy `personal/env.sh` and source it:

```bash
export CGM_ORIENT_DIR=/path/to/orientation_helpers   # orient_m61.py, pm_general.py
export CGM_STYLE_DIR=/path/to/styling_helpers        # common.py
export CGM_PYTHON=/path/to/python                     # python with yt + trident
export CGM_CUTOUT=/path/to/snapshot_or_cutout.hdf5    # yt-loadable input
export CGM_DATA_ROOT=/path/to/scratch/cgm_movie       # heavy outputs (NOT in the repo)
# Slurm:
export SBATCH_ACCOUNT=<your-account>
export SBATCH_PARTITION=<your-partition>
```

Then edit the **GALAXY block** in [`scripts/movie_config.py`](scripts/movie_config.py) for
your target: centre, virial radius, disk normal, systemic velocity, observed inclination,
and the sightline azimuth. The colormap limits, ion set, and the three segment definitions
also live in that one file.

## Running the pipeline

Submit from the repository root so the relative `logs/` and manifest paths resolve.

```bash
source personal/env.sh            # or export the CGM_* vars yourself

# 0. (recommended) smoke tests — validate line tokens, geometry, one full frame, motion
sbatch slurm/smoke_a.sbatch       # 10-ion spectrum stack at the fiducial sightline
sbatch slurm/smoke_d.sbatch       # one assembled frame + a 2x2 contact sheet

# 1. enumerate keyframes + render frames -> manifest_{proj,spec,frames}.csv
$CGM_PYTHON scripts/build_manifest.py

# 2. precompute projection maps   (array size = rows in manifest_proj.csv)
sbatch slurm/01_projections.sbatch

# 3. precompute rays + spectra     (strided chunks; cutout loaded once per chunk)
sbatch slurm/02_spectra.sbatch

# 4. assemble frames               (array size = rows in manifest_frames.csv)
sbatch slurm/03_frames.sbatch

# 5. encode to mp4 (50/40/30/24/20 fps)
sbatch slurm/04_encode.sbatch
```

Set each array's upper bound to `(#rows in the manifest − 1)` — `build_manifest.py` prints the
counts. `scripts/recovery_driver.sh` resumes a partial run (repairs missing spectra, then
re-submits frames + encode without a brittle `afterok` dependency).

## Repository layout

```
scripts/
  movie_config.py          # all configuration (paths via env, galaxy block, ions, segments)
  build_manifest.py        # keyframe + render-frame manifests
  movie_geom.py            # view basis + sightline geometry (run directly for a self-test)
  precompute_projection.py # off-axis maps + photometric g/r/i stellar inset  -> NPZ
  movie_spectra.py         # Trident ray + 10 single-transition velocity spectra -> HDF5
  render_spectra_panel.py  # the right-hand 10-ion stack
  assemble_frame.py        # composite one final 1920x1080 frame
  run_*.py / repair_*.py   # per-row Slurm workers + spectra repair
  recovery_driver.sh       # resume a partial run
  smoke_{a,c,d,e}.py       # validation tests
slurm/                     # sbatch wrappers + shared env.sh
results/                   # example movie + results notes
```

Heavy/per-run outputs (`data/`, `logs/`, the manifests, extra mp4s) are git-ignored and
regenerable; `personal/` holds local-only material and is never committed.

## Adapting to your own galaxy / simulation

1. Point `CGM_CUTOUT` at a snapshot/cutout `yt` can load, and set `CGM_DATA_ROOT`.
2. Fill in the GALAXY block in `movie_config.py` (centre, `RVIR_KPC`, `DISK_NORMAL`,
   `SUBHALO_VEL`, `OBS_INC_DEG`, `QSO_PHI_DEG`, little-*h*).
3. Adjust `HALF_WIDTH_KPC`, `DEPTH_KPC`, `NPIX`, the fixed colormap limits, the `IONS` list,
   and the per-segment ρ/inclination/azimuth ranges to taste.
4. Run the smoke tests first; then the full pipeline.

## License

[MIT](LICENSE).
