#!/bin/bash
read JP JS JF JE < /home/tsingh65/cgm-absorption-movie/logs/pipeline_jobids.txt
L=/home/tsingh65/cgm-absorption-movie
PY=/home/tsingh65/.conda/envs/trident/bin/python
export PYTHONPATH=/scratch/tsingh65/m61-tng/scripts:/home/tsingh65/finesst-codes/code/figure2:$L/scripts:$PYTHONPATH
export MPLBACKEND=Agg MPLCONFIGDIR=/tmp/mpl_rec
# 1) wait for spectra array to finish
while squeue -j "$JS" -h 2>/dev/null | grep -q .; do sleep 30; done
echo "SPEC_DONE $(date)  spec H5=$(find /data/sborthak/m61/edinburgh_movie/spectra -name 'spec_*.h5'|wc -l)/457"
# 2) repair any missing spectra (cutout once)
cd $L/scripts && $PY repair_missing_spec.py > $L/logs/repair_spec.log 2>&1
echo "REPAIR_DONE  NPZ=$(find /data/sborthak/m61/edinburgh_movie/projections -name 'proj_0*.npz'|wc -l)/298  spec=$(find /data/sborthak/m61/edinburgh_movie/spectra -name 'spec_*.h5'|wc -l)/457"
# 3) submit frames (NO dependency; all inputs present) + encode (afterany)
JF2=$(sbatch --parsable $L/slurm/03_frames.sbatch)
JE2=$(sbatch --parsable --dependency=afterany:$JF2 $L/slurm/04_encode.sbatch)
echo "RESUBMIT FRAMES=$JF2 ENCODE=$JE2"
echo "$JP $JS $JF2 $JE2" > $L/logs/pipeline_jobids.txt
echo "RECOVERY_LAUNCHED"
