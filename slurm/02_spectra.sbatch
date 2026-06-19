#!/bin/bash
#SBATCH --job-name=cgm_spec
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=96G --time=01:30:00
#SBATCH --array=0-39%40           # NCHUNKS-1; cutout loaded once per chunk
#SBATCH --output=logs/spec_%A_%a.out
#SBATCH --error=logs/spec_%A_%a.err
# Set SBATCH_ACCOUNT / SBATCH_PARTITION in your env (see slurm/env.sh). Submit from repo root.
REPO="${CGM_REPO:-${SLURM_SUBMIT_DIR:-$(pwd)}}"; source "$REPO/slurm/env.sh"
export MPLCONFIGDIR=/tmp/mpl_s_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}; mkdir -p "$MPLCONFIGDIR"
NCHUNKS=40
cd "$REPO/scripts"
"$PY" run_spec_chunk.py "$SLURM_ARRAY_TASK_ID" "$NCHUNKS"
