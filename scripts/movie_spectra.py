"""Trident ray + per-line raw velocity spectra for the CGM movie.

For each sightline (ray): generate, per ion, a raw flux-vs-velocity spectrum over a custom
+/-VEL_PAD window centred on the single chosen transition (no instrument LSF, no noise),
with use_doppler_redshift_only=True and the systemic velocity subtracted from the axis:
    flux = exp(-tau) ;  v = -(C*(lambda/rest - 1)) - v_sys     (+v = receding)
"""
from __future__ import annotations
import sys, math, inspect
from pathlib import Path
import numpy as np
import h5py

sys.path.insert(0, str(Path(__file__).parent))
import movie_config as C

C_KMS = C.C_KMS


def validate_tokens(verbose=True):
    """Return {ion_key: working_token}. Uses a FRESH LineDatabase per token (parse_subset
    accumulates!) and requires exactly ONE transition inside +/-VEL_PAD of the panel rest
    wavelength (no doublet contamination). Raises if any ion cannot be resolved cleanly."""
    from trident.line_database import LineDatabase
    resolved = {}
    table = []
    for d in C.IONS:
        rest = d["rest_A"]; chosen = None; n_in = None
        for tok in d["tokens"]:
            ldb = LineDatabase(C.LINE_LIST)              # FRESH per token
            try:
                subset = ldb.parse_subset([tok])
            except Exception:
                subset = []
            in_window = [ln for ln in subset
                         if abs(-C_KMS * (float(ln.wavelength) / rest - 1.0)) <= C.VEL_PAD_KMS]
            if len(in_window) == 1:
                chosen = tok; n_in = 1; break
        table.append((d["key"], d["tokens"], chosen, n_in, len(subset) if 'subset' in dir() else 0))
        if chosen is None:
            raise RuntimeError(f"No single-clean-line token for {d['key']} among {d['tokens']}")
        resolved[d["key"]] = chosen
    if verbose:
        print("Token resolution (fresh DB, exactly 1 line in +/-1500 km/s):")
        for key, toks, chosen, n_in, _ in table:
            print(f"  {key:14s} -> '{chosen}'  ({n_in} clean line)   [tried {toks}]")
    return resolved


def build_ray(ds, start_ckpch, end_ckpch, ray_h5, ion_list=None):
    """Build a Trident ray with all ion fields. Returns the ray-file path."""
    import trident, yt
    if ion_list is None:
        ion_list = C.SPECTRA_ION_LIST
    Path(ray_h5).parent.mkdir(parents=True, exist_ok=True)
    trident.make_simple_ray(
        ds,
        start_position=ds.arr(np.asarray(start_ckpch, float), "code_length"),
        end_position=ds.arr(np.asarray(end_ckpch, float), "code_length"),
        data_filename=str(ray_h5),
        lines=ion_list,
        ftype="gas",
        fields=[("gas", "density"), ("gas", "temperature"), ("gas", "metallicity")],
    )
    return str(ray_h5)


def make_line_velocity_spectrum(ray_ds, token, rest_A, v_sys_kms,
                                v_pad_kms=C.VEL_PAD_KMS, dv_kms=C.DV_KMS):
    """Raw flux & velocity for a single transition (no instrument, doppler-only)."""
    import trident
    half_A = rest_A * v_pad_kms / C_KMS
    dlam_A = rest_A * dv_kms / C_KMS
    sg = trident.SpectrumGenerator(lambda_min=rest_A - half_A,
                                   lambda_max=rest_A + half_A,
                                   dlambda=dlam_A,
                                   line_database=C.LINE_LIST)
    kw = dict(lines=[token], use_peculiar_velocity=True)
    if "use_doppler_redshift_only" in inspect.signature(sg.make_spectrum).parameters:
        kw["use_doppler_redshift_only"] = True
    sg.make_spectrum(ray_ds, **kw)
    lam = np.asarray(sg.lambda_field, float)
    tau = np.asarray(sg.tau_field, float)
    flux = np.exp(-tau)
    vel = -(C_KMS * (lam / rest_A - 1.0)) - v_sys_kms      # +v = receding
    return vel, flux, tau


def generate_movie_spectra(ray_ds, v_sys_kms, out_h5, tokens, meta=None):
    """Write all-ion velocity spectra for one sightline to HDF5."""
    Path(out_h5).parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(out_h5, "w") as f:
        f.attrs["v_sys_los_kms"] = float(v_sys_kms)
        f.attrs["convention"] = "v = -(C*(lam/rest-1)) - v_sys ; +v=receding"
        f.attrs["use_doppler_redshift_only"] = True
        f.attrs["use_peculiar_velocity"] = True
        if meta:
            for k, v in meta.items():
                f.attrs[k] = v
        g = f.create_group("by_line")
        diag = {}
        for i, d in enumerate(C.IONS):
            tok = tokens[d["key"]]
            vel, flux, tau = make_line_velocity_spectrum(ray_ds, tok, d["rest_A"], v_sys_kms)
            gl = g.create_group(d["key"])
            gl.attrs["ion"] = d["ion"]; gl.attrs["token"] = tok
            gl.attrs["rest_A"] = d["rest_A"]; gl.attrs["ip_order"] = i
            gl.create_dataset("vel", data=vel.astype("float32"))
            gl.create_dataset("flux", data=flux.astype("float32"))
            gl.create_dataset("tau", data=tau.astype("float32"))
            m = (vel > -C.VEL_WINDOW_KMS) & (vel < C.VEL_WINDOW_KMS)
            diag[d["key"]] = (float(flux[m].min()) if m.any() else np.nan, float(tau.max()))
    return diag
