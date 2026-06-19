#!/bin/bash
#SBATCH --job-name=cgm_smokeE
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=96G --time=00:40:00
#SBATCH --output=logs/smokeE_%j.out
#SBATCH --error=logs/smokeE_%j.err
# Set SBATCH_ACCOUNT / SBATCH_PARTITION in your env (see slurm/env.sh). Submit from repo root.
REPO="${CGM_REPO:-${SLURM_SUBMIT_DIR:-$(pwd)}}"; source "$REPO/slurm/env.sh"
export MPLCONFIGDIR=/tmp/mpl_cgmE_${SLURM_JOB_ID}; mkdir -p "$MPLCONFIGDIR"
cd "$REPO/scripts"
"$PY" smoke_e.py
