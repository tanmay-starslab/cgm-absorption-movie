#!/bin/bash
#SBATCH --job-name=cgm_smokeA
#SBATCH --partition=public
#SBATCH --account=grp_sborthak
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=96G
#SBATCH --time=01:30:00
#SBATCH --output=/home/tsingh65/cgm-absorption-movie/logs/smokeA_%j.out
#SBATCH --error=/home/tsingh65/cgm-absorption-movie/logs/smokeA_%j.err

echo "=== SMOKE A start $(date) on $(hostname) JOBID=$SLURM_JOB_ID ==="
export MPLBACKEND=Agg
export MPLCONFIGDIR=/tmp/mpl_cgm_$SLURM_JOB_ID; mkdir -p $MPLCONFIGDIR
export PYTHONPATH=/scratch/tsingh65/m61-tng/scripts:/home/tsingh65/cgm-absorption-movie/scripts:$PYTHONPATH
cd /home/tsingh65/cgm-absorption-movie/scripts
/home/tsingh65/.conda/envs/trident/bin/python smoke_a.py
echo "=== SMOKE A end $(date) exit=$? ==="
