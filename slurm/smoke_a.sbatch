#!/bin/bash
#SBATCH --job-name=cgm_smokeA
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=96G --time=01:30:00
#SBATCH --output=logs/smokeA_%j.out
#SBATCH --error=logs/smokeA_%j.err
# Set SBATCH_ACCOUNT / SBATCH_PARTITION in your env (see slurm/env.sh). Submit from repo root.
REPO="${CGM_REPO:-${SLURM_SUBMIT_DIR:-$(pwd)}}"; source "$REPO/slurm/env.sh"
export MPLCONFIGDIR=/tmp/mpl_cgmA_${SLURM_JOB_ID}; mkdir -p "$MPLCONFIGDIR"
cd "$REPO/scripts"
"$PY" smoke_a.py
