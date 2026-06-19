#!/bin/bash
#SBATCH --job-name=cgm_proj
#SBATCH --partition=htc
#SBATCH --account=grp_sborthak
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=96G --time=00:50:00
#SBATCH --array=0-298%80
#SBATCH --output=/home/tsingh65/cgm-absorption-movie/logs/proj_%A_%a.out
#SBATCH --error=/home/tsingh65/cgm-absorption-movie/logs/proj_%A_%a.err
export MPLBACKEND=Agg MPLCONFIGDIR=/tmp/mpl_p_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}; mkdir -p $MPLCONFIGDIR
export PYTHONPATH=/scratch/tsingh65/m61-tng/scripts:/home/tsingh65/finesst-codes/code/figure2:/home/tsingh65/cgm-absorption-movie/scripts:$PYTHONPATH
cd /home/tsingh65/cgm-absorption-movie/scripts
/home/tsingh65/.conda/envs/trident/bin/python run_proj_row.py $SLURM_ARRAY_TASK_ID
