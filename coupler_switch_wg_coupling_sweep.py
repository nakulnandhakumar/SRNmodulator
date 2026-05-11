import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
from ring_resonator.coupler_switch_supermode_run import run_single

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
y_sweep = np.linspace(0, 1.5e-6, 40)

results = []

# ============================================================
# SWEEP
# ============================================================

for y_vertical in y_sweep:

    result = run_single(
        pcm_material_coupler="SiO2 (Glass) - Palik",
        pcm_material_bus="SiO2 (Glass) - Palik",
        g=g,
        t_gap_pcm=t_gap_pcm,
        t_pcm=t_pcm,
        coupling="lateral",
        y_coupler_center=y_vertical
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

    print(
        f"dy = {y_vertical*1e6:.3f} um | "
        f"kappa = {kappa:.3e} 1/m | "
        f"D = {D:.3e}"
    )

# ============================================================
# DATAFRAME
# ============================================================

df = pd.DataFrame(results)
print(df)

# ============================================================
# PLOT
# ============================================================

plt.figure(figsize=(7,5))
plt.plot(df["y_vertical_um"], df["kappa_per_m"])
plt.xlabel("Vertical displacement (um)")
plt.ylabel("Coupling coefficient kappa (1/m)")
plt.title("Residual Coupling During Pull-Away")
plt.grid(True)
plt.show()