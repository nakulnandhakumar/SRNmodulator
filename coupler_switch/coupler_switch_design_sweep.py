import numpy as np
import pandas as pd
import sys
from coupler_switch_supermode import run_single
from coupler_switch_phase_correction import run_coupling_phase_correction
from coupler_switch_config import WG_COUPLING_CONFIG
import copy
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]
import time
import warnings
import os

warnings.filterwarnings(
    "ignore",
    message=r".*invalid escape sequence.*",
    category=SyntaxWarning
)

# ============================================================
# INITIALIZE LUMERICAL
# ============================================================

supermode = lumapi.MODE(
    hide=False,
    project=r"./lumerical/mode/supermode.lms"
)

# ============================================================
# LOAD CORRECT LSF SCRIPT
# ============================================================

coupling_direction = WG_COUPLING_CONFIG["coupling_direction"]
pcm_loading_direction = WG_COUPLING_CONFIG["pcm_loading_direction"]

# Determine which LSF script to use based on coupling and PCM loading directions
if coupling_direction == "lateral":

    if pcm_loading_direction == "top_pcm":
        script_path = (
            r"./lumerical/mode/"
            r"coupler_switch_lateralcpl_toppcm_supermode.lsf"
        )
    elif pcm_loading_direction == "side_pcm":
        script_path = (
            r"./lumerical/mode/"
            r"coupler_switch_lateralcpl_sidepcm_supermode.lsf"
        )
    else:
        raise ValueError(
            f'Unknown PCM loading direction: '
            f'{pcm_loading_direction}'
        )

elif coupling_direction == "vertical":

    if pcm_loading_direction == "top_pcm":
        script_path = (
            r"./lumerical/mode/"
            r"coupler_switch_verticalcpl_toppcm_supermode.lsf"
        )
    elif pcm_loading_direction == "side_pcm":
        script_path = (
            r"./lumerical/mode/"
            r"coupler_switch_verticalcpl_sidepcm_supermode.lsf"
        )
    else:
        raise ValueError(
            f'Unknown PCM loading direction: '
            f'{pcm_loading_direction}'
        )
        
else:
    raise ValueError(
        f'Unknown coupling direction: '
        f'{coupling_direction}'
    )

# Read lsf script
with open(script_path) as f:
    coupler_switch_supermode_script = f.read()

# ============================================================
# SWEEP PARAMETERS
# ============================================================

t_gap_pcm_values = np.arange(0, 41, 5) * 1e-9
t_pcm_values = np.arange(5, 41, 5) * 1e-9
gap_values = np.arange(300, 401, 10) * 1e-9

results = []

# ============================================================
# PROGRESS TRACKING
# ============================================================

total_iterations = len(t_pcm_values) * len(gap_values) * len(t_gap_pcm_values)
iteration = 0
global_start = time.time()

# ============================================================
# SAVE DIRECTORY SETUP
# ============================================================

save_dir = (
    f"./coupler_switch/coupler_switch_design_sweep_results/"
    f"{coupling_direction}_coupling/"
    f"{pcm_loading_direction}"
)

os.makedirs(save_dir, exist_ok=True)

# Filename parameters
W_nm = int(WG_COUPLING_CONFIG["W"] * 1e9)
H_nm = int(WG_COUPLING_CONFIG["H"] * 1e9)

g_min_nm = int(gap_values[0] * 1e9)
g_max_nm = int(gap_values[-1] * 1e9)

t_pcm_min_nm = int(t_pcm_values[0] * 1e9)
t_pcm_max_nm = int(t_pcm_values[-1] * 1e9)

t_gap_min_nm = int(t_gap_pcm_values[0] * 1e9)
t_gap_max_nm = int(t_gap_pcm_values[-1] * 1e9)

polarization = WG_COUPLING_CONFIG["polarization"]

filename = (
    f"design_"
    f"{polarization}_"
    f"W{W_nm}nm_"
    f"H{H_nm}nm_"
    f"g{g_min_nm}-{g_max_nm}nm_"
    f"tpcm{t_pcm_min_nm}-{t_pcm_max_nm}nm_"
    f"tgap{t_gap_min_nm}-{t_gap_max_nm}nm.csv"
)

save_path = os.path.join(save_dir, filename)

# Partial save file
partial_save_path = os.path.join(
    save_dir,
    "PARTIAL_" + filename
)

partial_save_every = 10

# ============================================================
# PARAMETER SWEEP
# ============================================================
try:
    for t_pcm in t_pcm_values:
        for g in gap_values:
            for t_gap_pcm in t_gap_pcm_values:
                
                # Progress tracking
                iteration += 1
                iter_start = time.time()
                
                # ------------------------------------------------
                # Create config copies
                # ------------------------------------------------
                
                antisym_config = copy.deepcopy(WG_COUPLING_CONFIG)
                sym_config = copy.deepcopy(WG_COUPLING_CONFIG)
                
                # ------------------------------------------------
                # Update geometry
                # ------------------------------------------------

                antisym_config["g"] = g
                antisym_config["t_gap_pcm"] = t_gap_pcm
                antisym_config["t_pcm"] = t_pcm

                sym_config["g"] = g
                sym_config["t_gap_pcm"] = t_gap_pcm
                sym_config["t_pcm"] = t_pcm
                
                # ----------------------------------------------
                # Waveguide positions based on coupling direction
                # ----------------------------------------------

                if coupling_direction == "lateral":

                    antisym_config["x_coupler_center"] = -(antisym_config["W"]/2 + antisym_config["g"]/2)
                    antisym_config["x_bus_center"] = (antisym_config["W"]/2 + antisym_config["g"]/2)

                    antisym_config["y_coupler_center"] = 0
                    antisym_config["y_bus_center"] = 0

                    sym_config["x_coupler_center"] = -(sym_config["W"]/2 + sym_config["g"]/2)
                    sym_config["x_bus_center"] = (sym_config["W"]/2 + sym_config["g"]/2)

                    sym_config["y_coupler_center"] = 0
                    sym_config["y_bus_center"] = 0

                elif coupling_direction == "vertical":

                    antisym_config["x_coupler_center"] = 0
                    antisym_config["x_bus_center"] = 0

                    antisym_config["y_coupler_center"] = (antisym_config["H"]/2 + antisym_config["g"]/2)
                    antisym_config["y_bus_center"] = -(antisym_config["H"]/2 + antisym_config["g"]/2)

                    sym_config["x_coupler_center"] = 0
                    sym_config["x_bus_center"] = 0

                    sym_config["y_coupler_center"] = (sym_config["H"]/2 + sym_config["g"]/2)
                    sym_config["y_bus_center"] = -(sym_config["H"]/2 + sym_config["g"]/2)

                else:
                    raise ValueError(f"Unknown coupling direction: {coupling_direction}")

                # ------------------------------------------------
                # Update PCM states
                # ------------------------------------------------

                antisym_config["pcm_mat_coupler"] = "SBS Amorphous"
                antisym_config["pcm_mat_bus"] = "SBS Crystalline"

                sym_config["pcm_mat_coupler"] = "SBS Crystalline"
                sym_config["pcm_mat_bus"] = "SBS Crystalline"

                # -------------------------------------------------
                # Run both states in Lumerical and extract results
                # -------------------------------------------------

                antisym = run_single(
                    config=antisym_config,
                    lum_project=supermode,
                    lsf_script=coupler_switch_supermode_script
                )

                sym = run_single(
                    config=sym_config,
                    lum_project=supermode,
                    lsf_script=coupler_switch_supermode_script
                )

                if antisym is None or sym is None:
                    continue
                    
                # If PCM overlap is too high, results may be inaccurate due to non-perturbative effects
                if (
                    antisym["eta_pcm_coupler_1"] > 0.15 or 
                    antisym["eta_pcm_bus_1"] > 0.15 or
                    antisym["eta_pcm_coupler_2"] > 0.15 or 
                    antisym["eta_pcm_bus_2"] > 0.15 or
                    sym["eta_pcm_coupler_1"] > 0.15 or 
                    sym["eta_pcm_bus_1"] > 0.15 or
                    sym["eta_pcm_coupler_2"] > 0.15 or 
                    sym["eta_pcm_bus_2"] > 0.15
                ):
                    continue

                # ---------------------------------
                # PHASE-CORRECTED COUPLING LENGTH
                # ---------------------------------
                phase_adjustment = run_coupling_phase_correction(
                    lum_project=supermode,
                    lsf_script=coupler_switch_supermode_script,

                    coupling_direction=WG_COUPLING_CONFIG["coupling_direction"],

                    polarization=WG_COUPLING_CONFIG["polarization"],

                    W=WG_COUPLING_CONFIG["W"],
                    H=WG_COUPLING_CONFIG["H"],

                    g=g,

                    Omega_sym=sym["Omega"],
                    R=15e-6
                )

                # phase correction from the tail region of the coupling profile
                theta_tail = phase_adjustment["theta_tail_rad"]

                # corrected straight coupling length
                L = phase_adjustment["Lc_corrected_um"] * 1e-6

                # ------------------------------
                # ACTUAL POWER TRANSFER
                # ------------------------------
                alpha_antisym = antisym["loss_eff"] * 100 / (10 * np.log10(np.e))  # dB/cm → 1/m
                alpha_sym  = sym["loss_eff"]  * 100 / (10 * np.log10(np.e))
                
                # total accumulated coupling phase
                theta_antisym = antisym["Omega"] * L + theta_tail
                theta_sym = sym["Omega"] * L + theta_tail

                # power transfer based on coupling strength and phase
                P_antisym = (1 - antisym["D"]**2) * np.sin(theta_antisym)**2
                P_sym = (1 - sym["D"]**2) * np.sin(theta_sym)**2
                
                # Account for losses over the length L
                P_antisym *= np.exp(-alpha_antisym * L)
                P_sym  *= np.exp(-alpha_sym  * L)

                # Avoid log(0)
                P_antisym_safe = max(P_antisym, 1e-12)
                P_sym_safe = max(P_sym, 1e-12)

                ER_dB = 10 * np.log10(P_sym_safe / P_antisym_safe)

                # ------------------------------
                # STORE RESULTS
                # ------------------------------
                results.append({
                    "g_nm": g * 1e9,
                    "t_pcm_nm": t_pcm * 1e9,
                    "t_gap_pcm_nm": t_gap_pcm * 1e9,

                    "D_antisym": antisym["D"],
                    "D_sym": sym["D"],
                    "delta_D": sym["D"] - antisym["D"],

                    "Amax_antisym": antisym["A_max"],
                    "Amax_sym": sym["A_max"],

                    "Omega_antisym": antisym["Omega"],
                    "Omega_sym": sym["Omega"],

                    "eta_pcm_avg_antisym": antisym["eta_pcm_avg"],
                    "eta_pcm_avg_sym": sym["eta_pcm_avg"],

                    "loss_eff_antisym": antisym["loss_eff"],
                    "loss_eff_sym": sym["loss_eff"],

                    "sym_mode1": sym["mode1"],
                    "sym_mode2": sym["mode2"],
                    "antisym_mode1": antisym["mode1"],
                    "antisym_mode2": antisym["mode2"],

                    # REAL DEVICE METRICS
                    "L_corrected_design_um": L * 1e6,
                    "theta_tail_rad": theta_tail,
                    "P_antisym": P_antisym,
                    "P_sym": P_sym,
                    "ER_dB": ER_dB,
                })
                
                # ============================================================
                # PARTIAL SAVE
                # ============================================================

                if iteration % partial_save_every == 0:

                    partial_df = pd.DataFrame(results)
                    partial_df.to_csv(partial_save_path, index=False)

                    print(f"Partial save completed ({len(results)} results)")
                
                # ------------------------------
                # PROGRESS UPDATE
                # ------------------------------

                elapsed = time.time() - global_start
                avg_time = elapsed / iteration
                remaining_iterations = total_iterations - iteration

                eta_seconds = int(avg_time * remaining_iterations)
                
                eta_hours = eta_seconds // 3600
                eta_minutes = (eta_seconds % 3600) // 60
                eta_secs = eta_seconds % 60

                percent = 100 * iteration / total_iterations

                print(
                    f"[{iteration}/{total_iterations}] "
                    f"{percent:.1f}% complete | "
                    f"ETA: {eta_hours}h {eta_minutes}m {eta_secs}s"
                )
                
finally:

    # Emergency save on crash/interruption
    partial_df = pd.DataFrame(results)
    partial_df.to_csv(partial_save_path,index=False)

    print(f"\nEmergency partial save written to:\n{partial_save_path}")

# ============================================================
# SAVE RESULTS
# ============================================================

results_df = pd.DataFrame(results)

# Save CSV
results_df.to_csv(save_path, index=False)