"""
modulator_overlap.py
--------------------

Core physics calculation.

Computes:
    - Δn_eff per volt
    - Effective χ² via EFISH
    - VpiL
    - Mode-weighted χ² average

Inputs:
    - Electrostatics fields (DEVICE)
    - Optical mode fields (MODE)
    - Geometry parameters

Major assumptions:

1. EFISH model:
       χ²_eff = (3/2) χ³ E_DC

2. χ³ is constant in SRN
3. Only SRN core contributes to nonlinearity
4. HfO2 and SiO2 are linear dielectrics
5. No carrier effects
6. No free-carrier absorption
7. No thermal effects
8. Small-signal AC regime
9. 2D cross-sectional approximation

Numerical steps:
    - Interpolate electrostatics onto optical grid
    - Build material masks
    - Compute Δε map
    - Perform overlap integrals
    - Extract VpiL

All spatial integration is Riemann sum:
    dA = dx * dy

This is the physics core of the project.
"""

import numpy as np
import pandas as pd
from scipy.interpolate import griddata


def compute_modulator_overlap():
    """
    Compute Δn_eff, χ²_eff, and Vπ·L for a given gap g (nm).

    Parameters
    ----------
    params : dict
        Dictionary containing the modulator parameters.

    Returns
    -------
    results : dict
        Dictionary containing:
        - dneff_per_V
        - chi2_eff_avg_mV
        - chi2_eff_avg_pmV
        - VpiL_Vm
        - VpiL_Vcm
        - lum (full dataframe)
    """
    # ============================================================
    # USER SETTINGS
    # ============================================================
    
    lam0 = 1.55e-6
    eps0 = 8.854e-12

    # ============================================================
    # FILE PATHS
    # ============================================================

    LUM_ESTAT_PATH = (
        f"modulator_data/lumerical_electrostatics/"
        f"modulator_electrostatics.csv"
    )

    LUM_MODE_PATH = (
        f"modulator_data/lumerical_mode/"
        f"modulator_mode.csv"
    )

    # ============================================================
    # GEOMETRY PARAMETERS (meters)
    # ============================================================
    Vdc = 1
    W = 380e-9
    H = 550e-9
    metal_t = 300e-9
    w_shield = 230e-9
    t_shield_gapR = 550e-9
    t_shield_gapL = 550e-9
    g = 2e-6 - (W/2) - w_shield

    # ---- Global parameters ----
    tBOX         = 3e-6
    tCLAD        = 2e-6
    metal_w      = 1e-6
    Xext         = 6e-6
    Ytop_margin  = 2e-6
    Ybot_margin  = 2e-6

    # ---- Derived positions ----
    y_BOX_top = tBOX
    y_BOX_bottom = 0 - Ybot_margin

    y_clad_bottom = tBOX
    y_clad_top = tBOX + tCLAD + Ytop_margin

    y_core_center = tBOX + H/2
    y_core_bottom = tBOX
    y_core_top = tBOX + H

    y_metal_center     = y_core_bottom + metal_t/2
    y_metal_top        = y_core_bottom + metal_t

    y_span = tBOX + tCLAD + Ytop_margin + Ybot_margin
    y_center = -Ybot_margin + y_span/2

    # Metal is separated from the shield by gap g
    x_metal_L  = -(W/2 + w_shield + g + metal_w/2)
    x_metal_R  =  (W/2 + w_shield + g + metal_w/2)

    # ============================================================
    # LOAD LUMERICAL ELECTROSTATICS
    # ============================================================

    estat = pd.read_csv(LUM_ESTAT_PATH)

    # ============================================================
    # LOAD LUMERICAL MODE DATA
    # ============================================================

    mode = pd.read_csv(LUM_MODE_PATH)

    if "E2" not in mode.columns:
        raise ValueError("Expected column 'E2' in Lumerical CSV.")

    # ============================================================
    # INTERPOLATE ELECTROSTATICS → OPTICAL (LUMERICAL GRID)
    # ============================================================

    # Source points: electrostatics mesh
    pts = np.column_stack((
        estat["x_m"].values,
        estat["y_m"].values
    ))

    # Target points: optical mode grid
    tgt = np.column_stack((
        mode["x_m"].values,
        mode["y_m"].values
    ))

    lum = pd.DataFrame({
        "x_m": mode["x_m"].values,
        "y_m": mode["y_m"].values,
    })

    # --- DC fields ---
    lum["EDCx"] = griddata(
        pts, estat["EDCx"].values, tgt, method="linear"
    )
    lum["EDCy"] = griddata(
        pts, estat["EDCy"].values, tgt, method="linear"
    )

    # --- AC fields (per 1 V) ---
    lum["EACx_1V"] = griddata(
        pts, estat["EACx_1V"].values, tgt, method="linear"
    )
    lum["EACy_1V"] = griddata(
        pts, estat["EACy_1V"].values, tgt, method="linear"
    )

    # ============================================================
    # NaN HANDLING (safe zero-fill for fields)
    # ============================================================

    field_cols = [
        "EDCx", "EDCy",
        "EACx_1V", "EACy_1V",
    ]

    for col in field_cols:
        n_nan = lum[col].isna().sum()
        if n_nan > 0:
            print(f"Warning: {n_nan} NaNs in {col}, replacing with 0")
            lum[col] = lum[col].fillna(0.0)

    # ============================================================
    # REGION MASKS
    # ============================================================

    # -----------------------------------------------------------
    # SLOT (EO polymer core)
    # -----------------------------------------------------------
    slot_mask = (
        (np.abs(lum["x_m"]) <= W/2) &
        (lum["y_m"] >= y_core_bottom) &
        (lum["y_m"] <= y_core_top)
    )

    # -----------------------------------------------------------
    # RIDGES (SiN left + right)
    # -----------------------------------------------------------

    # Left ridge: spans [-W/2 - w_shield, -W/2]
    ridge_left_mask = (
        (lum["x_m"] >= -(W/2 + w_shield)) &
        (lum["x_m"] <= -(W/2)) &
        (lum["y_m"] >= y_core_bottom) &
        (lum["y_m"] <= y_core_top)
    )

    # Right ridge: spans [W/2, W/2 + w_shield]
    ridge_right_mask = (
        (lum["x_m"] >= (W/2)) &
        (lum["x_m"] <= (W/2 + w_shield)) &
        (lum["y_m"] >= y_core_bottom) &
        (lum["y_m"] <= y_core_top)
    )

    ridge_mask = ridge_left_mask | ridge_right_mask

    # -----------------------------------------------------------
    # BOX (bottom oxide)
    # -----------------------------------------------------------
    BOX_mask = (
        (lum["y_m"] >= y_BOX_bottom) &
        (lum["y_m"] <= y_BOX_top)
    )

    # -----------------------------------------------------------
    # CLADDING (top polymer)
    # -----------------------------------------------------------
    cladding_mask = (
        (lum["y_m"] >= y_clad_bottom) &
        (lum["y_m"] <= y_clad_top)
    )
    
    # -----------------------------------------------------------
    # CLEANUP (avoid overlaps)
    # -----------------------------------------------------------

    # Remove slot + ridges from cladding
    cladding_mask = cladding_mask & ~(slot_mask | ridge_mask)

    # Remove ridges/slot from BOX (shouldn't overlap but safe)
    BOX_mask = BOX_mask & ~(slot_mask | ridge_mask)

    
    # ============================================================
    # DELTA EPSILON MAP
    # ============================================================

    # ------------------------------------------------------------
    # χ² spatial map (poled EO polymer only)
    # ------------------------------------------------------------

    # initialize
    lum["chi2"] = 0.0
    n_polymer = 1.65

    # ---- HARDCODE VALUES (you can tune these) ----
    chi2_polymer = 60e-12 * n_polymer**4  # [m/V] e.g. 50 pm/V

    # assign χ² to EO polymer regions
    lum.loc[slot_mask, "chi2"] = chi2_polymer
    lum.loc[cladding_mask, "chi2"] = chi2_polymer
    
    # ------------------------------------------------------------
    # Δε calculation
    # ------------------------------------------------------------
    Eproj = lum["EACx_1V"]  # assume poling along x
    lum["Deps"] = eps0 * lum["chi2"] * Eproj

    # ============================================================
    # OPTICAL PERMITTIVITY MAP
    # ============================================================

    n_SiO2 = 1.44
    n_polymer = 1.65
    n_SRN  = 2.5

    epsr_SiO2 = n_SiO2**2
    epsr_polymer = n_polymer**2
    epsr_SRN  = n_SRN**2

    lum["epsr_opt"] = epsr_polymer
    lum.loc[slot_mask, "epsr_opt"] = epsr_polymer
    lum.loc[cladding_mask, "epsr_opt"] = epsr_polymer      
    lum.loc[ridge_mask, "epsr_opt"] = epsr_SRN  
    lum.loc[BOX_mask, "epsr_opt"] = epsr_SiO2
    
    # ============================================================
    # DELTA Neff OVERLAP 
    # ============================================================

    lum["E2"] = mode["E2"]
    w    = lum["E2"].to_numpy(float)
    deps = lum["Deps"].to_numpy(float)
    epsr = lum["epsr_opt"].to_numpy(float)

    x_u = np.sort(lum["x_m"].unique())
    y_u = np.sort(lum["y_m"].unique())

    dx = np.median(np.diff(x_u))
    dy = np.median(np.diff(y_u))
    dA = dx * dy

    num = np.sum(deps * w) * dA
    den = 2 * np.sum(eps0 * epsr * w) * dA

    dneff_per_V = num / den

    # ============================================================
    # Vpi L
    # ============================================================

    VpiL_Vm  = lam0 / (2.0 * dneff_per_V)
    VpiL_Vcm = VpiL_Vm * 100

    # ============================================================
    # Return results
    # ============================================================
    
    return {
        "dneff_per_V": dneff_per_V,
        "VpiL_Vm": VpiL_Vm,
        "VpiL_Vcm": VpiL_Vcm,
        "lum": lum,
    }