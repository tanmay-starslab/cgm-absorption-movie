#!/bin/bash
#SBATCH --job-name=cgm_regen
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=48G --time=00:30:00
#SBATCH --array=0-456%80          # upper bound = (#rows in manifest_spec.csv - 1)
#SBATCH --output=logs/regen_%A_%a.out
#SBATCH --error=logs/regen_%A_%a.err
# Set SBATCH_ACCOUNT / SBATCH_PARTITION in your env (see slurm/env.sh). Submit from repo root.
REPO="${CGM_REPO:-${SLURM_SUBMIT_DIR:-$(pwd)}}"; source "$REPO/slurm/env.sh"
export MPLCONFIGDIR=/tmp/mpl_rg_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}; mkdir -p "$MPLCONFIGDIR"
cd "$REPO/scripts"
"$PY" regen_spec_one.py "$SLURM_ARRAY_TASK_ID"
