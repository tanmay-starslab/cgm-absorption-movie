#!/bin/bash
#SBATCH --job-name=cgm_smokeD
#SBATCH --partition=htc
#SBATCH --account=grp_sborthak
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=96G --time=01:30:00
#SBATCH --output=/home/tsingh65/cgm-absorption-movie/logs/smokeD_%j.out
#SBATCH --error=/home/tsingh65/cgm-absorption-movie/logs/smokeD_%j.err
echo "=== SMOKE D start $(date) on $(hostname) ==="
export MPLBACKEND=Agg MPLCONFIGDIR=/tmp/mpl_cgmD_$SLURM_JOB_ID; mkdir -p $MPLCONFIGDIR
export PYTHONPATH=/scratch/tsingh65/m61-tng/scripts:/home/tsingh65/finesst-codes/code/figure2:/home/tsingh65/cgm-absorption-movie/scripts:$PYTHONPATH
cd /home/tsingh65/cgm-absorption-movie/scripts
/home/tsingh65/.conda/envs/trident/bin/python smoke_d.py
echo "=== SMOKE D end $(date) exit=$? ==="
