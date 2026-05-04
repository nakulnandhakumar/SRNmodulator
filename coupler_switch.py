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

lam = 1.55e-6
supermode.putv("lambda", lam)

g = 200e-9  # keep fixed for now

t_pcm_values = np.array([5, 10, 15, 20, 25, 30, 40]) * 1e-9
t_gap_values = np.array([0, 2, 5, 10, 15, 20, 30]) * 1e-9

results = []

for t_pcm in t_pcm_values:
    for t_gap_pcm in t_gap_values:

        supermode.putv("g", g)
        supermode.putv("t_gap_pcm", t_gap_pcm)
        supermode.putv("t_pcm", t_pcm)

        off = run_single("SBS Amorphous", supermode, coupler_switch_supermode_script)
        on = run_single("SBS Crystalline", supermode, coupler_switch_supermode_script)

        if off is None or on is None:
            continue

        result = {
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

            "neff1_off": off["neff1"],
            "neff2_off": off["neff2"],
            "neff1_on": on["neff1"],
            "neff2_on": on["neff2"],
            
            "eta_pcm_avg_off": off["eta_pcm_avg"],
            "eta_pcm_avg_on": on["eta_pcm_avg"],
        }

        results.append(result)

results_df = pd.DataFrame(results)
results_df.to_csv("coupler_switch_pcm_sweep.csv", index=False)

print(results_df.sort_values("delta_Amax", ascending=False).head(10))