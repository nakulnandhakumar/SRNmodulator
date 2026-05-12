import numpy as np
import pandas as pd
import os
import sys
from scipy.interpolate import PchipInterpolator
from scipy.optimize import curve_fit
from coupler_switch_wg_coupling_sweep import wg_coupling_sweep


def run_coupling_phase_adjustment(lum_project, lsf_script, g=250e-9, Omega_sym=50233.970346, R=15e-6):
    # ==============================================
    # WAVEGUIDE COUPLING SWEEP
    # ==============================================

    # Check if file exists, if not run the sweep
    csv_path = f"coupler_switch/wg_coupling_sweep/g{int(g*1e9)}nm_.csv"
    if not os.path.exists(csv_path):
        print(f"Coupling sweep file not found at {csv_path}. Running sweep...")
        wg_coupling_sweep(lum_project, lsf_script, g=g)

    # Load the sweep results
    df = pd.read_csv(csv_path)
    y_um = df["y_vertical_um"].values
    kappa = df["kappa_per_m"].values

    # Use only clean region before mode-tracking gets weird
    clean = (y_um >= 0.0) & (y_um <= 0.9)
    y_clean = y_um[clean]
    k_clean = kappa[clean]

    # Smooth interpolation over measured region
    k_interp = PchipInterpolator(y_clean, k_clean)

    # Fit exponential tail over final clean segment
    tail_fit = (y_clean >= 0.55) & (y_clean <= 0.9)

    def exp_tail(y, A, b):
        return A * np.exp(-b * y)

    popt, _ = curve_fit(exp_tail, y_clean[tail_fit], k_clean[tail_fit], p0=[1e5, 5])
    A_fit, b_fit = popt

    def kappa_model(y_um):
        y_um = np.asarray(y_um)
        k = np.zeros_like(y_um, dtype=float)

        measured = y_um <= 0.9
        tail = y_um > 0.9

        k[measured] = k_interp(y_um[measured])

        # continuous tail after 0.9 um
        k_09 = k_interp(0.9)
        k[tail] = k_09 * np.exp(-b_fit * (y_um[tail] - 0.9))

        return k

    # =====================
    # BEND GEOMETRY
    # =====================

    # bend radius R defined in function
    kappa_threshold = 100  # 1/m, stop once coupling is negligible
    s_max = R * np.pi / 2  # Full quarter bend arc length

    s = np.linspace(0, s_max, 2000)

    # Pull-away displacement from circular bend
    d_m = R * (1 - np.cos(s / R))
    d_um_path = d_m * 1e6

    k_path = kappa_model(d_um_path)

    # Stop once kappa drops below threshold
    valid = k_path > kappa_threshold

    s_valid = s[valid]
    k_valid = k_path[valid]
    d_valid = d_um_path[valid]

    # =====================
    # PHASE CORRECTION
    # =====================
    theta_tail = np.trapz(k_valid, s_valid)

    # ==============================================
    # ORIGINAL PCM DESIGN VALUES
    # ==============================================

    # Omega_sym defined in function
    Lc_old = np.pi / (2 * Omega_sym)

    # ==============================================
    # CORRECTED STRAIGHT COUPLING LENGTH
    # ==============================================

    L_tail_equiv = theta_tail / Omega_sym
    Lc_corrected = Lc_old - L_tail_equiv

    # ==============================================
    # RETURN RESULTS
    # ==============================================

    results = {
        "Lc_old_um": Lc_old * 1e6,
        "theta_tail_rad": theta_tail,
        "L_tail_equiv_um": L_tail_equiv * 1e6,
        "Lc_corrected_um": Lc_corrected * 1e6
    }
    
    return results