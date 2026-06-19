#!/bin/bash
#SBATCH --job-name=cgm_frame
#SBATCH --partition=htc
#SBATCH --account=grp_sborthak
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=1 --mem=6G --time=00:25:00
#SBATCH --array=0-1649%300
#SBATCH --output=/home/tsingh65/cgm-absorption-movie/logs/frame_%A_%a.out
#SBATCH --error=/home/tsingh65/cgm-absorption-movie/logs/frame_%A_%a.err
export MPLBACKEND=Agg MPLCONFIGDIR=/tmp/mpl_f_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}; mkdir -p $MPLCONFIGDIR
export PYTHONPATH=/scratch/tsingh65/m61-tng/scripts:/home/tsingh65/finesst-codes/code/figure2:/home/tsingh65/cgm-absorption-movie/scripts:$PYTHONPATH
cd /home/tsingh65/cgm-absorption-movie/scripts
/home/tsingh65/.conda/envs/trident/bin/python run_frame_row.py $SLURM_ARRAY_TASK_ID
