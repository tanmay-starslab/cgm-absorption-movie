#!/bin/bash
#SBATCH --job-name=cgm_smokeE
#SBATCH --partition=htc
#SBATCH --account=grp_sborthak
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=96G --time=00:40:00
#SBATCH --output=/home/tsingh65/cgm-absorption-movie/logs/smokeE_%j.out
#SBATCH --error=/home/tsingh65/cgm-absorption-movie/logs/smokeE_%j.err
echo "=== SMOKE E start $(date) on $(hostname) ==="
export MPLBACKEND=Agg MPLCONFIGDIR=/tmp/mpl_cgmE_$SLURM_JOB_ID; mkdir -p $MPLCONFIGDIR
export PYTHONPATH=/scratch/tsingh65/m61-tng/scripts:/home/tsingh65/finesst-codes/code/figure2:/home/tsingh65/cgm-absorption-movie/scripts:$PYTHONPATH
cd /home/tsingh65/cgm-absorption-movie/scripts
/home/tsingh65/.conda/envs/trident/bin/python smoke_e.py
echo "=== SMOKE E end $(date) exit=$? ==="
