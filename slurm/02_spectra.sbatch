#!/bin/bash
#SBATCH --job-name=cgm_spec
#SBATCH --partition=htc
#SBATCH --account=grp_sborthak
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=96G --time=01:30:00
#SBATCH --array=0-39%40
#SBATCH --output=/home/tsingh65/cgm-absorption-movie/logs/spec_%A_%a.out
#SBATCH --error=/home/tsingh65/cgm-absorption-movie/logs/spec_%A_%a.err
export MPLBACKEND=Agg MPLCONFIGDIR=/tmp/mpl_s_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}; mkdir -p $MPLCONFIGDIR
export PYTHONPATH=/scratch/tsingh65/m61-tng/scripts:/home/tsingh65/finesst-codes/code/figure2:/home/tsingh65/cgm-absorption-movie/scripts:$PYTHONPATH
cd /home/tsingh65/cgm-absorption-movie/scripts
/home/tsingh65/.conda/envs/trident/bin/python run_spec_chunk.py $SLURM_ARRAY_TASK_ID 40
