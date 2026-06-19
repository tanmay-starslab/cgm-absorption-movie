#!/bin/bash
#SBATCH --job-name=cgm_smokeP
#SBATCH --partition=public
#SBATCH --account=grp_sborthak
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=96G --time=01:30:00
#SBATCH --output=/home/tsingh65/cgm-absorption-movie/logs/smokeP_%j.out
#SBATCH --error=/home/tsingh65/cgm-absorption-movie/logs/smokeP_%j.err
echo "=== SMOKE PROJ start $(date) on $(hostname) ==="
export MPLBACKEND=Agg MPLCONFIGDIR=/tmp/mpl_cgmP_$SLURM_JOB_ID; mkdir -p $MPLCONFIGDIR
export PYTHONPATH=/scratch/tsingh65/m61-tng/scripts:/home/tsingh65/finesst-codes/code/figure2:/home/tsingh65/cgm-absorption-movie/scripts:$PYTHONPATH
cd /home/tsingh65/cgm-absorption-movie/scripts
/home/tsingh65/.conda/envs/trident/bin/python precompute_projection.py seg1 23.0 0.0 \
   /data/sborthak/m61/edinburgh_movie/projections/seg1/proj_fiducial_inc23_a0.npz
echo "=== SMOKE PROJ end $(date) exit=$? ==="
