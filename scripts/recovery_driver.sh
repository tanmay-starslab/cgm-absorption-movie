#!/bin/bash
# Resume helper: wait for the spectra array to finish, repair any missing spectra,
# then (re)submit frames + encode without a hard afterok dependency (robust to Slurm
# requeue artifacts). Configure via env (see slurm/env.sh / personal/env.sh).
set -u
REPO="${CGM_REPO:-$(cd "$(dirname "$0")/.." && pwd)}"
source "$REPO/slurm/env.sh"
DATA="${CGM_DATA_ROOT:-$REPO/data}"
read JP JS JF JE < "$REPO/logs/pipeline_jobids.txt"
export MPLCONFIGDIR=/tmp/mpl_rec; mkdir -p "$MPLCONFIGDIR"
NSPEC=$(( $(wc -l < "$REPO/manifest_spec.csv") - 1 ))
NPROJ=$(( $(wc -l < "$REPO/manifest_proj.csv") - 1 ))
# 1) wait for the spectra array to finish
while squeue -j "$JS" -h 2>/dev/null | grep -q .; do sleep 30; done
echo "SPEC_DONE $(date)  spec=$(find "$DATA/spectra" -name 'spec_*.h5' 2>/dev/null | wc -l)/$NSPEC"
# 2) repair any missing spectra (cutout loaded once)
cd "$REPO/scripts" && "$PY" repair_missing_spec.py > "$REPO/logs/repair_spec.log" 2>&1
echo "REPAIR_DONE  npz=$(find "$DATA/projections" -name 'proj_*.npz' 2>/dev/null | wc -l)/$NPROJ"
# 3) (re)submit frames + encode (afterany; all inputs already present)
JF2=$(sbatch --parsable "$REPO/slurm/03_frames.sbatch")
JE2=$(sbatch --parsable --dependency=afterany:$JF2 "$REPO/slurm/04_encode.sbatch")
echo "RESUBMIT FRAMES=$JF2 ENCODE=$JE2"
echo "$JP $JS $JF2 $JE2" > "$REPO/logs/pipeline_jobids.txt"
echo "RECOVERY_LAUNCHED"
