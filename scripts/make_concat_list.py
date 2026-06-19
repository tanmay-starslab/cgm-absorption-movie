import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); import pandas as pd, movie_config as C
df = pd.read_csv(C.REPO_ROOT / "manifest_frames.csv").sort_values("global_idx")
for p in df.frame_png:
    if os.path.exists(p): print(f"file '{p}'")
