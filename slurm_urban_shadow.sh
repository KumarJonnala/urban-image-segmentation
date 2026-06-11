#!/bin/bash

# Usage examples:
#
#   sbatch slurm_urban_shadow.sh                                           # full pipeline @ 250m
#   sbatch --export=COMMAND=all,TILE_SIZE=all       slurm_urban_shadow.sh  # full pipeline all sizes [100,250,500,1000]
#   sbatch --export=COMMAND=download,TILE_SIZE=all  slurm_urban_shadow.sh  # download all sizes
#   sbatch --export=COMMAND=segment,TILE_SIZE=all   slurm_urban_shadow.sh  # segment all sizes
#   sbatch --export=COMMAND=shadow,TILE_SIZE=all    slurm_urban_shadow.sh  # shadow all sizes
#   sbatch --export=COMMAND=download,TILE_SIZE=100  slurm_urban_shadow.sh  # download 100m only
#   sbatch --export=COMMAND=segment,TILE_SIZE=250   slurm_urban_shadow.sh  # segment 250m only
#   sbatch --export=COMMAND=shadow,TILE_SIZE=500    slurm_urban_shadow.sh  # shadow 500m only
#   sbatch --export=COMMAND=merge,TILE_SIZE=250     slurm_urban_shadow.sh  # merge FGBs at 250m
#   sbatch --export=COMMAND=render,TILE_SIZE=250    slurm_urban_shadow.sh  # render merged view
#   sbatch --export=COMMAND=status                  slurm_urban_shadow.sh  # check progress
#

#SBATCH --job-name=urban_shadow
#SBATCH --output=logs/job_%j.out
#SBATCH --error=logs/job_%j.err

#SBATCH --partition=gpu
#SBATCH --nodelist=ant1
#SBATCH --gres=shard:8
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=8:00:00

# --- environment ---
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p logs

pip install -q -r requirements.txt

# --- pipeline ---
# Edit TILE_SIZE and COMMAND below, or pass as sbatch --export= variables
TILE_SIZE=${TILE_SIZE:-250}
COMMAND=${COMMAND:-all}

echo "Starting urban-shadow-analysis pipeline"
echo "  Command   : $COMMAND"
echo "  Tile size : ${TILE_SIZE}m"
echo "  Node      : $SLURMD_NODENAME"
echo "  Job ID    : $SLURM_JOB_ID"
echo "  Time      : $(date -u '+%Y-%m-%d %H:%M UTC')"

if [ "$TILE_SIZE" = "all" ]; then
    python3 pipeline.py "$COMMAND" --all-sizes
else
    python3 pipeline.py "$COMMAND" --tile-size "$TILE_SIZE"
fi

echo "Done: $(date -u '+%Y-%m-%d %H:%M UTC')"
