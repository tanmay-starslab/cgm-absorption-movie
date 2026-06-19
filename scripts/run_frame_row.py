"""Assemble one frame from manifest_frames.csv row $1."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, "/scratch/tsingh65/m61-tng/scripts")
sys.path.insert(0, "/home/tsingh65/finesst-codes/code/figure2")
import pandas as pd, movie_config as C, assemble_frame as AF
r = pd.read_csv(C.REPO_ROOT / "manifest_frames.csv").iloc[int(sys.argv[1])]
Path(r.frame_png).parent.mkdir(parents=True, exist_ok=True)
AF.assemble(str(r.proj_npz), str(r.spec_h5), float(r.rho_kpc), float(r.inc_deg), float(r.alpha_deg), str(r.frame_png))
print("wrote", r.frame_png)
