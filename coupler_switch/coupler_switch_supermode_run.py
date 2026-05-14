import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
from coupler_switch_supermode import run_single
from coupler_switch_config import WG_COUPLING_CONFIG
import copy
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]
import warnings

warnings.filterwarnings(
    "ignore",
    message=r".*invalid escape sequence.*",
    category=SyntaxWarning
)

# ===================== INIT =====================

supermode = lumapi.MODE(
    hide=False,
    project=r"./lumerical/mode/supermode.lms"
)

# Choose script based on coupling direction
if WG_COUPLING_CONFIG["coupling_direction"] == "lateral":
    script_path = (
        r"./lumerical/mode/coupler_switch_lateral_supermode.lsf"
    )

elif WG_COUPLING_CONFIG["coupling_direction"] == "vertical":
    script_path = (
        r"./lumerical/mode/coupler_switch_vertical_supermode.lsf"
    )
else:
    raise ValueError(
        f'Unknown coupling direction: '
        f'{WG_COUPLING_CONFIG["coupling_direction"]}'
    )

with open(script_path) as f:
    coupler_switch_supermode_script = f.read()

# ===================== CONFIG COPIES =====================

# Asymmetric state
antisym_config = copy.deepcopy(WG_COUPLING_CONFIG)
antisym_config["pcm_mat_coupler"] = "SBS Amorphous"
antisym_config["pcm_mat_bus"] = "SBS Crystalline"

# Symmetric state
sym_config = copy.deepcopy(WG_COUPLING_CONFIG)
sym_config["pcm_mat_coupler"] = "SBS Crystalline"
sym_config["pcm_mat_bus"] = "SBS Crystalline"

# ===================== RUN BOTH STATES =====================

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