# Shared environment for the CGM-movie Slurm jobs.
# Each sbatch script sources this. Configure by exporting CGM_* before `sbatch`
# (e.g. `source personal/env.sh`), or edit the fallbacks below.
#
# Slurm account/partition are NOT hard-coded in the #SBATCH headers: set them with
#   export SBATCH_ACCOUNT=<your-account>
#   export SBATCH_PARTITION=<your-partition>
# (Slurm reads these env vars for any directive you don't pass on the command line),
# or add `--account=... --partition=...` to your `sbatch` invocation.

REPO="${CGM_REPO:-${SLURM_SUBMIT_DIR:-$(pwd)}}"
PY="${CGM_PYTHON:-python}"                       # python with yt + trident
ORIENT_DIR="${CGM_ORIENT_DIR:-}"                 # dir with orient_m61.py, pm_general.py
STYLE_DIR="${CGM_STYLE_DIR:-}"                   # dir with common.py

export PYTHONPATH="$ORIENT_DIR:$STYLE_DIR:$REPO/scripts:$PYTHONPATH"
export MPLBACKEND=Agg
mkdir -p "$REPO/logs"
