#!/bin/bash
#SBATCH --job-name=cgm_encode
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=8G --time=00:20:00
#SBATCH --output=logs/encode_%j.out
#SBATCH --error=logs/encode_%j.err
# Set SBATCH_ACCOUNT / SBATCH_PARTITION in your env (see slurm/env.sh). Submit from repo root.
REPO="${CGM_REPO:-${SLURM_SUBMIT_DIR:-$(pwd)}}"; source "$REPO/slurm/env.sh"
# Load ffmpeg however your site provides it (module/conda/system):
module load ffmpeg-6.0-gcc-12.1.0 2>/dev/null || true
cd "$REPO"
"$PY" scripts/make_concat_list.py > frames.txt
for FPS in 50 40 30 24 20; do
  ffmpeg -y -r $FPS -f concat -safe 0 -i frames.txt -c:v libx264 -profile:v high \
    -pix_fmt yuv420p -crf 18 -preset slow -vf "scale=1920:1080:flags=lanczos,format=yuv420p" \
    -movflags +faststart "results/cgm_movie_${FPS}fps.mp4"
done
echo "encoded mp4s in results/"
