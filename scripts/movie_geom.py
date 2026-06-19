"""Geometry / orientation for the CGM movie.

Source of truth = orient_m61.build_R_bases + fixed_observer_galaxy_alpha_rotation.
For a keyframe (mode, inc, alpha):
    east = R_cur[0,:],  north = R_cur[1,:],  los = R_cur[2,:]   (raw rows; match orient CSV)
    v_sys = dot(SubhaloVel, los_unit)
QSO sightline at sky (rho, phi):
    anchor = center + rho*(cos phi * east_u + sin phi * north_u)
    ray = anchor +/- (1 Rvir)*los_u ;  marker_image = (rho cos phi, rho sin phi)

Run directly for the self-test:  python movie_geom.py
"""
from __future__ import annotations
import sys, math
import numpy as np

sys.path.insert(0, "/scratch/tsingh65/m61-tng/scripts")
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import orient_m61
import movie_config as C


def unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def view_basis(inc_deg, alpha_deg, mode=C.MODE, n_hat=None):
    """Return dict with raw + unit (east, north, los), v_sys, R_cur for one orientation."""
    if n_hat is None:
        n_hat = C.DISK_NORMAL
    R_nf, R_fl, axis_nf, axis_fl = orient_m61.build_R_bases(n_hat, float(inc_deg), 0.0)
    if mode == "noflip":
        R_base, axis = R_nf, axis_nf
    else:
        R_base, axis = R_fl, axis_fl
    R_cur = orient_m61.fixed_observer_galaxy_alpha_rotation(R_base, axis, float(alpha_deg))
    east_raw  = np.array([1.0, 0, 0]) @ R_cur
    north_raw = np.array([0, 1.0, 0]) @ R_cur
    los_raw   = np.array([0, 0, 1.0]) @ R_cur
    los_u   = unit(los_raw)
    north_u = unit(north_raw - np.dot(north_raw, los_u) * los_u)   # like pm_general
    east_u  = unit(np.cross(north_u, los_u))
    v_sys   = float(np.dot(C.SUBHALO_VEL, los_u))
    return dict(R_cur=R_cur,
                east_raw=east_raw, north_raw=north_raw, los_raw=los_raw,
                east=east_u, north=north_u, los=los_u,
                v_sys=v_sys, inc_deg=float(inc_deg), alpha_deg=float(alpha_deg), mode=mode)


def sightline(vb, rho_kpc, phi_deg=C.QSO_PHI_DEG, half_kpc=C.RVIR_KPC):
    """3D ray endpoints + image-plane marker for impact parameter rho along sky azimuth phi.
    Uses the RAW east/north rows so the anchor matches orient_m61's QSO placement exactly."""
    phi = math.radians(phi_deg)
    east_u  = unit(vb["east_raw"]); north_u = unit(vb["north_raw"]); los_u = vb["los"]
    rho_hat = math.cos(phi) * east_u + math.sin(phi) * north_u
    rho_hat = unit(rho_hat - np.dot(rho_hat, los_u) * los_u)        # keep perp to los
    anchor = C.CENTER_KPC + rho_kpc * rho_hat
    start  = anchor - half_kpc * los_u
    end    = anchor + half_kpc * los_u
    # image-plane marker in the (east_u, north_u) display frame used by the projection
    rel = anchor - C.CENTER_KPC
    marker_xy = (float(np.dot(rel, vb["east"])), float(np.dot(rel, vb["north"])))
    return dict(anchor_kpc=anchor, start_kpc=start, end_kpc=end,
                start_ckpch=start * C.TNG_H, end_ckpch=end * C.TNG_H,
                anchor_ckpch=anchor * C.TNG_H, rho_kpc=rho_kpc, phi_deg=phi_deg,
                marker_xy_kpc=marker_xy)


# ── Self-test ──────────────────────────────────────────────────────────────────
def _selftest():
    sys.path.insert(0, "/scratch/tsingh65/m61-tng/scripts")
    import pm_general as pmg
    print("=== movie_geom self-test (sub 488530) ===")
    maxe_los = maxe_north = 0.0
    for alpha in [0, 17, 90, 213, 359]:
        vb = view_basis(C.OBS_INC_DEG, alpha, mode="noflip")
        g = pmg.get_geometry(C.SID, "noflip", alpha)
        e_los   = np.linalg.norm(vb["los"]   - g["los"])
        e_north = np.linalg.norm(vb["north"] - g["north"])
        maxe_los = max(maxe_los, e_los); maxe_north = max(maxe_north, e_north)
        print(f"  alpha={alpha:3d}: |los-CSV|={e_los:.2e}  |north-CSV|={e_north:.2e}")
    print(f"  MAX los err={maxe_los:.2e}  north err={maxe_north:.2e}  "
          f"{'PASS' if max(maxe_los,maxe_north)<1e-6 else 'FAIL'}")
    # anchor vs compute_endpoints at fiducial rho
    vb = view_basis(C.OBS_INC_DEG, 0, mode="noflip")
    sl = sightline(vb, 25.558333340264905)
    ce = pmg.compute_endpoints(C.SID, "noflip", 0, 25.558333340264905, C.RVIR_KPC)
    da = np.linalg.norm(sl["anchor_kpc"] - ce["anchor_kpc"])
    ds = np.linalg.norm(sl["start_kpc"]  - ce["start_kpc"])
    print(f"  anchor vs compute_endpoints: |Δanchor|={da:.3e} kpc  |Δstart|={ds:.3e} kpc  "
          f"{'PASS' if max(da,ds)<1e-3 else 'FAIL'}")
    # v_sys at a few orientations (should change with inc & alpha)
    for inc, al in [(23, 0), (90, 0), (0, 0), (23, 180)]:
        vb = view_basis(inc, al); print(f"  v_sys(inc={inc:3d},a={al:3d}) = {vb['v_sys']:+8.3f} km/s")


if __name__ == "__main__":
    _selftest()
