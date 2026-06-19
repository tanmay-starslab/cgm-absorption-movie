"""Assemble one frame from manifest_frames.csv row $1."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, os.environ.get("CGM_ORIENT_DIR", ""))  # orient_m61, pm_general
sys.path.insert(0, os.environ.get("CGM_STYLE_DIR", ""))  # common.py
import pandas as pd, movie_config as C, assemble_frame as AF
r = pd.read_csv(C.REPO_ROOT / "manifest_frames.csv").iloc[int(sys.argv[1])]
Path(r.frame_png).parent.mkdir(parents=True, exist_ok=True)
AF.assemble(str(r.proj_npz), str(r.spec_h5), float(r.rho_kpc), float(r.inc_deg), float(r.alpha_deg), str(r.frame_png))
print("wrote", r.frame_png)
