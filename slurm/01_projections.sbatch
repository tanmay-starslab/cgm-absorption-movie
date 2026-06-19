#!/bin/bash
#SBATCH --job-name=cgm_proj
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=96G --time=00:50:00
#SBATCH --array=0-298%80          # upper bound = (#rows in manifest_proj.csv - 1)
#SBATCH --output=logs/proj_%A_%a.out
#SBATCH --error=logs/proj_%A_%a.err
# Set SBATCH_ACCOUNT / SBATCH_PARTITION in your env (see slurm/env.sh). Submit from repo root.
REPO="${CGM_REPO:-${SLURM_SUBMIT_DIR:-$(pwd)}}"; source "$REPO/slurm/env.sh"
export MPLCONFIGDIR=/tmp/mpl_p_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}; mkdir -p "$MPLCONFIGDIR"
cd "$REPO/scripts"
"$PY" run_proj_row.py "$SLURM_ARRAY_TASK_ID"
