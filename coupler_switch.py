import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
from ring_resonator.coupler_switch_supermode_run import run_single
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]

# Initialize Lumerical MODE for the ring filter waveguide
supermode = lumapi.MODE(
            hide=False,
            project=r"./lumerical/mode/supermode.lms"
        )

with open(r"./lumerical/mode/coupler_switch_supermode.lsf") as f:
    coupler_switch_supermode_script = f.read()

# ===================== SWEEP PARAMETERS =====================

# Fix spacing between PCM and waveguide, and sweep coupling gap as well as PCM thickness
t_gap_pcm = 0e-9

t_pcm_values = np.arange(5, 51, 2) * 1e-9
gap_values   = np.arange(200, 301, 5) * 1e-9


results = []

for t_pcm in t_pcm_values:
    for g in gap_values:
        
        # Run both states for the current parameter combination
        antisym = run_single("SBS Amorphous", g=g, t_gap_pcm=t_gap_pcm, t_pcm=t_pcm, 
                         lum_project=supermode, coupling="vertical", lsf_script=coupler_switch_supermode_script)
        sym  = run_single("SBS Crystalline", g=g, t_gap_pcm=t_gap_pcm, t_pcm=t_pcm, 
                         lum_project=supermode, coupling="vertical", lsf_script=coupler_switch_supermode_script)

        if antisym is None or sym is None:
            continue
            
        # If PCM overlap is too high, results may be inaccurate due to non-perturbative effects
        if (antisym["eta_pcm_left_1"] > 0.15 or antisym["eta_pcm_right_1"] > 0.15 or
                antisym["eta_pcm_left_2"] > 0.15 or antisym["eta_pcm_right_2"] > 0.15 or
                sym["eta_pcm_left_1"] > 0.15 or sym["eta_pcm_right_1"] > 0.15 or
                sym["eta_pcm_left_2"] > 0.15 or sym["eta_pcm_right_2"] > 0.15):
            continue

        # =====================
        # DESIGN LENGTH (from ON)
        # =====================
        L = np.pi / (2 * sym["Omega"])   # meters

        # =====================
        # ACTUAL POWER TRANSFER
        # =====================
        alpha_antisym = antisym["loss_eff"] * 100 / (10 * np.log10(np.e))  # dB/cm → 1/m
        alpha_sym  = sym["loss_eff"]  * 100 / (10 * np.log10(np.e))
        
        P_antisym = (1 - antisym["D"]**2) * np.sin(antisym["Omega"] * L)**2
        P_sym  = (1 - sym["D"]**2)  * np.sin(sym["Omega"]  * L)**2
        
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
            "L_design_um": L * 1e6,
            "P_antisym": P_antisym,
            "P_sym": P_sym,
            "ER_dB": ER_dB,
        })

results_df = pd.DataFrame(results)
results_df.to_csv("ring_resonator/coupler_switch_pcm_sweep.csv", index=False)

good = results_df[
    (results_df["P_sym"] > 0.95) &
    (results_df["P_antisym"] < 0.10)
]

print("\n========== GOOD DESIGNS ==========")
print(good[["t_pcm_nm", "t_gap_pcm_nm", "D_antisym", "D_sym", "Omega_antisym", "Omega_sym", "eta_pcm_avg_antisym", "eta_pcm_avg_sym", "L_design_um", "P_antisym", "P_sym", "ER_dB"]])