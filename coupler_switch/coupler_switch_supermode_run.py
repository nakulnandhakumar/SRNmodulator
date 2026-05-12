import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
from coupler_switch.coupler_switch_supermode import run_single
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]
import time

# ===================== INIT =====================

supermode = lumapi.MODE(
    hide=False,
    project=r"./lumerical/mode/supermode.lms"
)

with open(r"./lumerical/mode/coupler_switch_supermode.lsf") as f:
    coupler_switch_supermode_script = f.read()

# ===================== PARAMETERS =====================

g = 250e-9
t_gap_pcm = 0e-9
t_pcm = 50e-9

# ===================== RUN BOTH STATES =====================

antisym = run_single(pcm_material_coupler="SBS Amorphous", pcm_material_bus="SBS Crystalline", y_coupler_center=0, g=g, t_gap_pcm=t_gap_pcm, t_pcm=t_pcm, lum_project=supermode, lsf_script=coupler_switch_supermode_script, coupling="lateral")
sym  = run_single(pcm_material_coupler="SBS Crystalline", pcm_material_bus="SBS Crystalline", y_coupler_center=0, g=g, t_gap_pcm=t_gap_pcm, t_pcm=t_pcm, lum_project=supermode, lsf_script=coupler_switch_supermode_script, coupling="lateral")

# ===================== RESULTS =====================

print("\n========== RESULTS ==========")

print("\nASYMMETRIC (NO COUPLING)")
for key, value in antisym.items():
    if isinstance(value, float):
        print(f"{key} = {value:.6f}")
    else:
        print(f"{key} = {value}")

print("\nSYMMETRIC (STRONG COUPLING)")
for key, value in sym.items():
    if isinstance(value, float):
        print(f"{key} = {value:.6f}")
    else:
        print(f"{key} = {value}")

if antisym and sym:

    # =====================
    # DESIGN LENGTH (from symmetric state)
    # =====================
    L = np.pi / (2 * sym["Omega"])   # meters

    # =====================
    # ACTUAL POWER TRANSFER
    # =====================
    P_antisym = (1 - antisym["D"]**2) * np.sin(antisym["Omega"] * L)**2
    P_sym  = (1 - sym["D"]**2)  * np.sin(sym["Omega"]  * L)**2

    # avoid log(0)
    P_sym_safe = max(P_sym, 1e-12)

    ER_dB = 10 * np.log10(P_sym_safe / P_antisym)

    # =====================
    # PRINT RESULTS
    # =====================
    print("\n========== SWITCHING ==========")
    print(f"L_design (um) = {L*1e6:.3f}")
    print(f"P_antisym = {P_antisym:.4f}")
    print(f"P_sym  = {P_sym:.4f}")
    print(f"ER (dB) = {ER_dB:.2f}")