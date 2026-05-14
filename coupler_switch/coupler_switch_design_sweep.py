import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
from coupler_switch_supermode import run_single
from coupler_switch_phase_adjustment import run_coupling_phase_adjustment
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]
import time
import warnings

warnings.filterwarnings(
    "ignore",
    message=r".*invalid escape sequence.*",
    category=SyntaxWarning
)

# Initialize Lumerical MODE for the ring filter waveguide
supermode = lumapi.MODE(
            hide=False,
            project=r"./lumerical/mode/supermode.lms"
        )

with open(r"./lumerical/mode/coupler_switch_lateral_supermode.lsf") as f:
    coupler_switch_supermode_script = f.read()

# ===================== SWEEP PARAMETERS =====================

# Fix spacing between PCM and waveguide, and sweep coupling gap as well as PCM thickness
t_gap_pcm_values = np.arange(0, 51, 5) * 1e-9   # 0 to 50 nm gap between PCM and waveguide, in steps of 5 nm
t_pcm_values = np.arange(5, 51, 5) * 1e-9   # PCM thickness from 5 to 50 nm, in steps of 5 nm
gap_values   = np.arange(200, 301, 10) * 1e-9   # Coupling gap from 200 to 400 nm, in steps of 10 nm

results = []

phase_cache = {}

# ===================== PROGRESS TRACKING =====================

total_iterations = len(t_pcm_values) * len(gap_values) * len(t_gap_pcm_values)
iteration = 0
global_start = time.time()

# ===================== PARAMETER SWEEP =====================

for t_pcm in t_pcm_values:
    for g in gap_values:
        for t_gap_pcm in t_gap_pcm_values:
            
            # Progress tracking
            iteration += 1
            iter_start = time.time()
        
            # Run both states for the current parameter combination
            antisym = run_single(pcm_material_coupler="SBS Amorphous", pcm_material_bus="SBS Crystalline", y_coupler_center=0, g=g, t_gap_pcm=t_gap_pcm, t_pcm=t_pcm, 
                            lum_project=supermode, lsf_script=coupler_switch_supermode_script, coupling="lateral")
            sym  = run_single(pcm_material_coupler="SBS Crystalline", pcm_material_bus="SBS Crystalline", y_coupler_center=0, g=g, t_gap_pcm=t_gap_pcm, t_pcm=t_pcm, 
                            lum_project=supermode, lsf_script=coupler_switch_supermode_script, coupling="lateral")

            if antisym is None or sym is None:
                continue
                
            # If PCM overlap is too high, results may be inaccurate due to non-perturbative effects
            if (antisym["eta_pcm_left_1"] > 0.15 or antisym["eta_pcm_right_1"] > 0.15 or
                    antisym["eta_pcm_left_2"] > 0.15 or antisym["eta_pcm_right_2"] > 0.15 or
                    sym["eta_pcm_left_1"] > 0.15 or sym["eta_pcm_right_1"] > 0.15 or
                    sym["eta_pcm_left_2"] > 0.15 or sym["eta_pcm_right_2"] > 0.15):
                continue

            # =====================
            # PHASE-CORRECTED COUPLING LENGTH
            # =====================
            
            if g not in phase_cache:
                phase_adjust = run_coupling_phase_adjustment(
                    lum_project=supermode,
                    lsf_script=coupler_switch_supermode_script,
                    g=g,
                    Omega_sym=sym["Omega"],
                    R=15e-6
                )

            theta_tail = phase_cache[g]["theta_tail_rad"]

            # corrected straight coupling length
            L = phase_adjust["Lc_corrected_um"] * 1e-6

            # =====================
            # ACTUAL POWER TRANSFER
            # =====================
            alpha_antisym = antisym["loss_eff"] * 100 / (10 * np.log10(np.e))  # dB/cm → 1/m
            alpha_sym  = sym["loss_eff"]  * 100 / (10 * np.log10(np.e))
            
            # total accumulated coupling phase
            theta_antisym = antisym["Omega"] * L + theta_tail
            theta_sym = sym["Omega"] * L + theta_tail

            P_antisym = (
                (1 - antisym["D"]**2)
                * np.sin(theta_antisym)**2
            )

            P_sym = (
                (1 - sym["D"]**2)
                * np.sin(theta_sym)**2
            )
            
            # Account for losses over the length L
            P_antisym *= np.exp(-alpha_antisym * L)
            P_sym  *= np.exp(-alpha_sym  * L)

            # Avoid log(0)
            P_sym_safe = max(P_sym, 1e-12)

            ER_dB = 10 * np.log10(P_sym_safe / P_antisym)

            # =====================
            # STORE RESULTS
            # =====================
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
            
            # =====================
            # PROGRESS UPDATE
            # =====================

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

results_df = pd.DataFrame(results)
results_df.to_csv("coupler_switch/coupler_switch_pcm_sweep.csv", index=False)