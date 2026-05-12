import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
from coupler_switch.coupler_switch_supermode import run_single
import time

sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]

# ============================================================
# INIT
# ============================================================

mode = lumapi.MODE(
    hide=False,
    project=r"./lumerical/mode/supermode.lms"
)

with open(r"./lumerical/mode/coupler_switch_supermode.lsf") as f:
    lsf_script = f.read()

# ============================================================
# SWEEP PARAMETERS
# ============================================================

g = 250e-9

t_gap_pcm = 0e-9
t_pcm = 50e-9

# vertical pull-away sweep
y_sweep = np.linspace(0, 0.9e-6, 40)

results = []

# ============================================================
# TIME TRACKING
# ============================================================

total_iterations = len(y_sweep)
global_start = time.time()
iteration = 0

# ============================================================
# SWEEP
# ============================================================

for y_vertical in y_sweep:

    # Progress tracking
    iteration += 1
    iter_start = time.time()
    
    # Run the simulation for the current vertical displacement
    result = run_single(
        pcm_material_coupler="SiO2 (Glass) - Palik",
        pcm_material_bus="SiO2 (Glass) - Palik",
        y_coupler_center=y_vertical,
        g=g,
        t_gap_pcm=t_gap_pcm,
        t_pcm=t_pcm,
        lum_project=mode,
        lsf_script=lsf_script,
        coupling="lateral"
    )

    if result is None:
        continue

    # identical-guide coupling coefficient
    kappa = result["Omega"]
    D = result["D"] # just for verification, should be near 0 for identical guides

    results.append({
        "y_vertical_um": y_vertical * 1e6,
        "kappa_per_m": kappa,
        "dneff": result["dneff"],
        "D": D
    })
    
    # ========================================================
    # Progress tracking
    # ========================================================

    elapsed = time.time() - global_start
    avg_time = elapsed / iteration
    remaining_iterations = total_iterations - iteration

    eta_seconds = int(avg_time * remaining_iterations)

    eta_hours = eta_seconds // 3600
    eta_minutes = (eta_seconds % 3600) // 60
    eta_secs = eta_seconds % 60

    percent = 100 * iteration / total_iterations

    print(
        f"dy = {y_vertical*1e6:.3f} um | "
        f"kappa = {kappa:.3e} 1/m | "
        f"D = {D:.3e} | "
        f"{percent:.1f}% complete | "
        f"ETA: {eta_hours}h {eta_minutes}m {eta_secs}s"
    )

# ============================================================
# DATAFRAME
# ============================================================

df = pd.DataFrame(results)

# Save to CSV
df.to_csv("coupler_switch/coupler_switch_wg_coupling_sweep.csv", index=False)