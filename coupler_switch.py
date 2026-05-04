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

g = 200e-9

t_pcm_values = np.array([5, 10, 15, 20, 25, 30, 40]) * 1e-9
t_gap_values = np.array([0, 2, 5, 10, 15, 20, 30]) * 1e-9

results = []

for t_pcm in t_pcm_values:
    for t_gap_pcm in t_gap_values:
        
        # Run both states for the current parameter combination
        off = run_single("SBS Amorphous", g=g, t_gap_pcm=t_gap_pcm, t_pcm=t_pcm, 
                         lum_project=supermode, lsf_script=coupler_switch_supermode_script)
        on  = run_single("SBS Crystalline", g=g, t_gap_pcm=t_gap_pcm, t_pcm=t_pcm, 
                         lum_project=supermode, lsf_script=coupler_switch_supermode_script)

        if off is None or on is None:
            continue
        
        # Check mode ordering consistency
        if off["mode1"] != 1 or off["mode2"] != 2:
            print("WARNING: mode ordering changed (OFF)")

        if on["mode1"] != 1 or on["mode2"] != 2:
            print("WARNING: mode ordering changed (ON)")
            
        # If PCM overlap is too high, results may be inaccurate due to non-perturbative effects
        if on["eta_pcm_avg"] > 0.25:
            print("WARNING: PCM overlap too high, results may be inaccurate")
            continue

        # Store results in a list of dictionaries
        results.append({
            "g_nm": g * 1e9,
            "t_pcm_nm": t_pcm * 1e9,
            "t_gap_pcm_nm": t_gap_pcm * 1e9,
            
            "D_off": off["D"],
            "D_on": on["D"],
            "delta_D": on["D"] - off["D"],
            
            "Amax_off": off["A_max"],
            "Amax_on": on["A_max"],
            "delta_Amax": off["A_max"] - on["A_max"],
            
            "Omega_off": off["Omega"],
            "Omega_on": on["Omega"],

            "eta_pcm_avg_off": off["eta_pcm_avg"],
            "eta_pcm_avg_on": on["eta_pcm_avg"],

            "on_mode1": on["mode1"],
            "on_mode2": on["mode2"],
            "off_mode1": off["mode1"],
            "off_mode2": off["mode2"],
            
            "Lmax_off_um": np.pi / (2 * off["Omega"]) * 1e6,
            "Lmax_on_um": np.pi / (2 * on["Omega"]) * 1e6,
        })

results_df = pd.DataFrame(results)
results_df.to_csv("ring_resonator/coupler_switch_pcm_sweep.csv", index=False)

print(results_df.sort_values("delta_Amax", ascending=False).head(10))