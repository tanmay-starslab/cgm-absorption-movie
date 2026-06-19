"""SMOKE E (1 frame): recompute fiducial projection with the colourful stellar mock + apply all
render-side tweaks (N_HI vmin10/vmax23, bigger colorbars, fixed info boxes). Reuse smoke-C spectra."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, "/scratch/tsingh65/m61-tng/scripts")
sys.path.insert(0, "/home/tsingh65/finesst-codes/code/figure2")
import movie_config as C
OUT = C.RESULTS / "smoke"; (OUT/"e_proj").mkdir(parents=True, exist_ok=True)
npz = str(OUT/"e_proj"/"fiducial_inc23_a0.npz")
sys.argv = ["x", "seg1", "23.0", "0.0", npz]
import precompute_projection as P; P.main()
import assemble_frame as AF
spec = str(OUT/"c_spec"/"spec_r030.0_i023.0_a000.0.h5")
out = str(OUT/"smokeE_frame.png")
AF.assemble(npz, spec, 30.0, 23.0, 0.0, out)
print("wrote", out)
