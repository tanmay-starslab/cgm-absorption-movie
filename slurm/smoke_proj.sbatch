#!/bin/bash
#SBATCH --job-name=cgm_smokeP
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=96G --time=01:30:00
#SBATCH --output=logs/smokeP_%j.out
#SBATCH --error=logs/smokeP_%j.err
# Set SBATCH_ACCOUNT / SBATCH_PARTITION in your env (see slurm/env.sh). Submit from repo root.
REPO="${CGM_REPO:-${SLURM_SUBMIT_DIR:-$(pwd)}}"; source "$REPO/slurm/env.sh"
export MPLCONFIGDIR=/tmp/mpl_cgmP_${SLURM_JOB_ID}; mkdir -p "$MPLCONFIGDIR"
cd "$REPO/scripts"
OUT="${CGM_DATA_ROOT:-$REPO/data}/projections/seg1/proj_fiducial.npz"; mkdir -p "$(dirname "$OUT")"
"$PY" precompute_projection.py seg1 23.0 0.0 "$OUT"
