import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from coupler_switch_supermode import run_single
import time
import copy
import os
from coupler_switch_config import WG_COUPLING_CONFIG

def phase_correction_coupling_sweep(
    lum_project,
    lsf_script,
    coupling_direction,
    W,
    H,
    g
):
    
    # ============================================================
    # SWEEP PARAMETERS
    # ============================================================

    # vertical/horizontal pull-away sweep
    pull_away_sweep = np.linspace(0, 0.9e-6, 40)

    results = []

    # ============================================================
    # TIME TRACKING
    # ============================================================

    total_iterations = len(pull_away_sweep)
    global_start = time.time()
    iteration = 0

    # ============================================================
    # SWEEP
    # ============================================================

    for pull_away in pull_away_sweep:

        iteration += 1

        config = copy.deepcopy(WG_COUPLING_CONFIG)
        
        config["coupling_direction"] = coupling_direction
        config["W"] = W
        config["H"] = H
        config["g"] = g

        # --------------------------------------------------------
        # Remove PCM physics entirely
        # --------------------------------------------------------

        config["pcm_mat_coupler"] = "SiO2 (Glass) - Palik"
        config["pcm_mat_bus"] = "SiO2 (Glass) - Palik"
        
        # --------------------------------------------------------
        # Compute waveguide centers
        # --------------------------------------------------------

        if config["coupling_direction"] == "lateral":

            config["x_coupler_center"] = -(W/2 + g/2)
            config["x_bus_center"] = (W/2 + g/2)

            config["y_coupler_center"] = pull_away
            config["y_bus_center"] = 0

        elif config["coupling_direction"] == "vertical":

            config["y_coupler_center"] = (H/2 + g/2)
            config["y_bus_center"] = -(H/2 + g/2)

            config["x_coupler_center"] = pull_away
            config["x_bus_center"] = 0

        else:
            raise ValueError(
                f'Unknown coupling direction: '
                f'{config["coupling_direction"]}'
            )

        result = run_single(
            config=config,
            lum_project=lum_project,
            lsf_script=lsf_script
        )

        if result is None:
            continue

        # identical-guide coupling coefficient
        kappa = result["Omega"]
        D = result["D"] # just for verification, should be near 0 for identical guides

        results.append({
            "pull_away_um": pull_away * 1e6,
            "kappa_per_m": kappa,
            "dneff": result["dneff"],
            "D": D
        })
        
        # ---------------------------------------------------------
        # Progress tracking
        # ---------------------------------------------------------

        elapsed = time.time() - global_start
        avg_time = elapsed / iteration
        remaining_iterations = total_iterations - iteration

        eta_seconds = int(avg_time * remaining_iterations)

        eta_hours = eta_seconds // 3600
        eta_minutes = (eta_seconds % 3600) // 60
        eta_secs = eta_seconds % 60

        percent = 100 * iteration / total_iterations

        print(
            f"pull away = {pull_away*1e6:.3f} um | "
            f"kappa = {kappa:.3e} 1/m | "
            f"D = {D:.3e} | "
            f"{percent:.1f}% complete | "
            f"ETA: {eta_hours}h {eta_minutes}m {eta_secs}s"
        )

    # ============================================================
    # SAVE RESULTS
    # ============================================================

    results_df = pd.DataFrame(results)

    # Create save directory based on coupling direction
    save_dir = (
        f"./phase_correction_coupling_sweep/"
        f"{coupling_direction}_coupling"
    )
    os.makedirs(save_dir, exist_ok=True)

    # Create filename based on key parameters
    W_nm = int(W * 1e9)
    H_nm = int(H * 1e9)
    g_nm = int(g * 1e9)

    filename = (
        f"pullaway_"
        f"W{W_nm}nm_"
        f"H{H_nm}nm_"
        f"g{g_nm}nm.csv"
    )

    # save results to CSV
    save_path = os.path.join(save_dir, filename)
    results_df.to_csv(save_path, index=False)
    
    return results_df