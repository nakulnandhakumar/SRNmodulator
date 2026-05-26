import numpy as np
import pandas as pd
import os
from scipy.interpolate import PchipInterpolator
from scipy.optimize import curve_fit
from coupler_switch_phase_correction_coupling_sweep import phase_correction_coupling_sweep

"""
This module computes the phase correction to the straight coupling length due 
to the non-ideal coupling tail in the bend region, based on a coupling sweep 
that characterizes the coupling coefficient as a function of pull-away distance.
"""
def run_coupling_phase_correction(
    lum_project,
    lsf_script,
    coupling_direction,
    polarization,
    W_bus,
    H_bus,
    W_coupler,
    H_coupler,
    g,
    Omega,
    R
):

    # ============================================================
    # PHASE SWEEP FILE PATH
    # ============================================================

    # Clamping waveguide dimensions to be identical even for asymmetric loading for now
    W_bus_nm = int(W_bus * 1e9)
    H_bus_nm = int(H_bus * 1e9)
    W_coupler_nm = int(W_bus * 1e9)
    H_coupler_nm = int(H_bus * 1e9)
    g_nm = int(g * 1e9)

    save_dir = (
        f"./coupler_switch/phase_correction_coupling_sweep/"
        f"{coupling_direction}_coupling"
    )

    filename = (
        f"pullaway_"
        f"{polarization}_"
        f"Wbus{W_bus_nm}nm_"
        f"Hbus{H_bus_nm}nm_"
        f"Wcpl{W_coupler_nm}nm_"
        f"Hcpl{H_coupler_nm}nm_"
        f"g{g_nm}nm.csv"
)

    csv_path = os.path.join(save_dir, filename)

    # ============================================================
    # RUN SWEEP IF FILE DOES NOT EXIST
    # ============================================================

    if not os.path.exists(csv_path):

        print(
            f"Coupling sweep file not found:\n"
            f"{csv_path}\n"
            f"Running coupling sweep..."
        )

        phase_correction_coupling_sweep(
            lum_project=lum_project,
            lsf_script=lsf_script,
            coupling_direction=coupling_direction,
            polarization=polarization,
            W_bus=W_bus,
            H_bus=H_bus,
            W_coupler=W_coupler,
            H_coupler=H_coupler,
            g=g
        )

    # Load the sweep results
    df = pd.read_csv(csv_path)
    pull_away_um = df["pull_away_um"].values
    kappa = df["kappa_per_m"].values

    # Use only clean region before mode-tracking gets weird
    clean = (pull_away_um >= 0.0) & (pull_away_um <= 0.9)
    pull_away_clean = pull_away_um[clean]
    k_clean = kappa[clean]

    # Smooth interpolation over measured region
    k_interp = PchipInterpolator(pull_away_clean, k_clean)

    # Fit exponential tail over final clean segment
    tail_fit = (pull_away_clean >= 0.55) & (pull_away_clean <= 0.9)

    def exp_tail(y, A, b):
        return A * np.exp(-b * y)

    popt, _ = curve_fit(exp_tail, pull_away_clean[tail_fit], k_clean[tail_fit], p0=[1e5, 5])
    A_fit, b_fit = popt

    def kappa_model(pull_away_um):
        pull_away_um = np.asarray(pull_away_um)
        k = np.zeros_like(pull_away_um, dtype=float)

        measured = pull_away_um <= 0.9
        tail = pull_away_um > 0.9

        k[measured] = k_interp(pull_away_um[measured])

        # continuous tail after 0.9 um
        k_09 = k_interp(0.9)
        k[tail] = k_09 * np.exp(-b_fit * (pull_away_um[tail] - 0.9))

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

    # Omega defined in function
    Lc_old = np.pi / (2 * Omega)

    # ==============================================
    # CORRECTED STRAIGHT COUPLING LENGTH
    # ==============================================

    L_tail_equiv = theta_tail / Omega
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