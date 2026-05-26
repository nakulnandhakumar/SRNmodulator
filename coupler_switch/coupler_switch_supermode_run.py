import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
from coupler_switch_supermode import run_single
from coupler_switch_phase_correction import run_coupling_phase_correction
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


# ============ LOAD CORRECT LSF SCRIPT =============

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

    elif pcm_loading_direction == "asym_pcm":
        script_path = (
            r"./lumerical/mode/"
            r"coupler_switch_verticalcpl_asympcm_supermode.lsf"
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

# ===================== CONFIG COPIES =====================

# Asymmetric state
antisym_config = copy.deepcopy(WG_COUPLING_CONFIG)
antisym_config["pcm_mat_coupler"] = "SBS Amorphous"
antisym_config["pcm_mat_bus"] = "SBS Crystalline"

# Symmetric state
sym_config = copy.deepcopy(WG_COUPLING_CONFIG)
sym_config["pcm_mat_coupler"] = "SBS Crystalline"
sym_config["pcm_mat_bus"] = "SBS Crystalline"


# ================== WAVEGUIDE POSITIONS ==================

coupling_direction = WG_COUPLING_CONFIG["coupling_direction"]

if coupling_direction == "lateral":

    antisym_config["x_coupler_center"] = -(antisym_config["W_coupler"]/2 + antisym_config["g"]/2)
    antisym_config["x_bus_center"] = (antisym_config["W_bus"]/2 + antisym_config["g"]/2)

    antisym_config["y_coupler_center"] = 0
    antisym_config["y_bus_center"] = 0

    sym_config["x_coupler_center"] = -(sym_config["W_coupler"]/2 + sym_config["g"]/2)
    sym_config["x_bus_center"] = (sym_config["W_bus"]/2 + sym_config["g"]/2)

    sym_config["y_coupler_center"] = 0
    sym_config["y_bus_center"] = 0

elif coupling_direction == "vertical":

    H_bus_antisym = antisym_config["H_bus"]
    H_coupler_antisym = antisym_config["H_coupler"]

    center_sep_antisym = (H_bus_antisym/2 + antisym_config["g"] + H_coupler_antisym/2)
    antisym_config["y_coupler_center"] = center_sep_antisym / 2
    antisym_config["y_bus_center"] = -(center_sep_antisym / 2)

    antisym_config["x_coupler_center"] = 0
    antisym_config["x_bus_center"] = 0

    H_bus_sym = sym_config["H_bus"]
    H_coupler_sym = sym_config["H_coupler"]

    center_sep_sym = (H_bus_sym/2 + sym_config["g"] + H_coupler_sym/2)
    sym_config["y_coupler_center"] = center_sep_sym / 2
    sym_config["y_bus_center"] = -(center_sep_sym / 2)

    sym_config["x_coupler_center"] = 0
    sym_config["x_bus_center"] = 0

else:
    raise ValueError(f"Unknown coupling direction: {coupling_direction}")

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

    # ============================================================
    # DETERMINE DESIGN STATE
    # ============================================================

    if sym["D"] <= antisym["D"]:
        design_state = sym
        design_state_name = "sym"
    else:
        design_state = antisym
        design_state_name = "antisym"

    print(f"\nDesign state = {design_state_name}")

    # ============================================================
    # PHASE-CORRECTED COUPLING LENGTH
    # ============================================================

    phase_adjustment = run_coupling_phase_correction(
        lum_project=supermode,
        lsf_script=coupler_switch_supermode_script,

        coupling_direction=WG_COUPLING_CONFIG["coupling_direction"],

        polarization=WG_COUPLING_CONFIG["polarization"],

        W_bus=WG_COUPLING_CONFIG["W_bus"],
        H_bus=WG_COUPLING_CONFIG["H_bus"],

        W_coupler=WG_COUPLING_CONFIG["W_coupler"],
        H_coupler=WG_COUPLING_CONFIG["H_coupler"],

        g=WG_COUPLING_CONFIG["g"],

        Omega=design_state["Omega"],

        R=WG_COUPLING_CONFIG["bend_radius"]
    )

    theta_tail = phase_adjustment["theta_tail_rad"]

    # Coupling length correction in meters
    L = phase_adjustment["Lc_corrected_um"] * 1e-6

    # ACTUAL POWER TRANSFER
    theta_antisym = antisym["Omega"] * L + theta_tail
    theta_sym = sym["Omega"] * L + theta_tail

    P_antisym = (1 - antisym["D"]**2) * np.sin(theta_antisym)**2
    P_sym = (1 - sym["D"]**2) * np.sin(theta_sym)**2
    
    # Include coupling loss from imaginary part of effective index
    alpha_antisym = antisym["loss_eff"] * 100 / (10 * np.log10(np.e))
    alpha_sym = sym["loss_eff"] * 100 / (10 * np.log10(np.e))

    P_antisym *= np.exp(-alpha_antisym * L)
    P_sym *= np.exp(-alpha_sym * L)

    # avoid log(0)
    P_sym_safe = max(P_sym, 1e-12)

    ER_dB = 10 * np.log10(P_sym_safe / P_antisym)

    # PRINT RESULTS
    print("\n========== SWITCHING ==========")
    print(f"L_design (um) = {L*1e6:.3f}")
    print(f"P_antisym = {P_antisym:.4f}")
    print(f"P_sym  = {P_sym:.4f}")
    print(f"ER (dB) = {ER_dB:.2f}")