#!/bin/bash
#SBATCH --job-name=cgm_encode
#SBATCH --partition=htc
#SBATCH --account=grp_sborthak
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=8G --time=00:20:00
#SBATCH --output=/home/tsingh65/cgm-absorption-movie/logs/encode_%j.out
#SBATCH --error=/home/tsingh65/cgm-absorption-movie/logs/encode_%j.err
module load ffmpeg-6.0-gcc-12.1.0
cd /home/tsingh65/cgm-absorption-movie
/home/tsingh65/.conda/envs/trident/bin/python scripts/make_concat_list.py > frames.txt
for FPS in 30 24 20; do
  ffmpeg -y -r $FPS -f concat -safe 0 -i frames.txt -c:v libx264 -profile:v high \
    -pix_fmt yuv420p -crf 18 -preset slow -vf "scale=1920:1080:flags=lanczos,format=yuv420p" \
    -movflags +faststart results/cgm_absorption_488530_${FPS}fps.mp4
done
echo "encoded mp4s in results/"
