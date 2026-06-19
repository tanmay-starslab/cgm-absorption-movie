# Example result

`cgm_movie_50fps.mp4` — an example render of the pipeline (1920×1080, H.264 / yuv420p,
`+faststart`). Example target: **TNG50-1 subhalo 488530** at *z* = 0; 1650 frames at 50 fps
(≈33 s).

**Left** — 4-quadrant off-axis projection (gas surface density, temperature, *N*<sub>HI</sub>,
rest-frame *v*<sub>LOS</sub>) + photometric *g/r/i* stellar inset + bold sightline marker +
25 kpc scalebar. **Right** — 10-ion absorption stack (H I → S XIV). The three continuous
segments sweep impact parameter ρ (150 → 2 kpc), inclination (edge-on ↔ face-on), and
azimuth α (0 → 360°).

The encode step (`slurm/04_encode.sbatch`) can emit additional playback speeds
(50/40/30/24/20 fps) from the same frames; only the 50 fps example is committed here. Heavy
per-run outputs live outside the repository under `$CGM_DATA_ROOT`.
