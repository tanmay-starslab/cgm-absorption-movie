"""Compute one projection from manifest_proj.csv row $1."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import pandas as pd, movie_config as C, precompute_projection as P
row = pd.read_csv(C.REPO_ROOT / "manifest_proj.csv").iloc[int(sys.argv[1])]
sys.argv = ["x", str(row.segment), str(float(row.inc_deg)), str(float(row.alpha_deg)), str(row.npz)]
P.main()
