#!/bin/bash
#SBATCH --job-name=cgm_frame
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=1 --mem=6G --time=00:25:00
#SBATCH --array=0-1649%300        # upper bound = (#rows in manifest_frames.csv - 1)
#SBATCH --output=logs/frame_%A_%a.out
#SBATCH --error=logs/frame_%A_%a.err
# Set SBATCH_ACCOUNT / SBATCH_PARTITION in your env (see slurm/env.sh). Submit from repo root.
REPO="${CGM_REPO:-${SLURM_SUBMIT_DIR:-$(pwd)}}"; source "$REPO/slurm/env.sh"
export MPLCONFIGDIR=/tmp/mpl_f_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}; mkdir -p "$MPLCONFIGDIR"
cd "$REPO/scripts"
"$PY" run_frame_row.py "$SLURM_ARRAY_TASK_ID"
