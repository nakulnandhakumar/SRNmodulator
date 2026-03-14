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
from material_properties import BREAKDOWN_FIELDS


def compute_modulator_overlap(params):
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
    chi3_SRN = 6e-19   # m^2 / V^2  (update if you refine this)

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

    # All units are in meters
    Vdc = params["Vdc"]
    g = params["g"]
    W = params["W"]
    H = params["H"]
    metal_t = params["metal_t"]
    t_shield_gapR = params["t_shield_gapR"]
    t_shield_gapL = params["t_shield_gapL"]
    t_shield_core = params["t_shield_core"]
    t_shield_metal = params["t_shield_metal"]

    dt_shield_gapR_1 = params["dt_shield_gapR_1"]
    dt_shield_gapR_2 = params["dt_shield_gapR_2"]
    dt_shield_gapR_3 = params["dt_shield_gapR_3"]

    dt_shield_gapL_1 = params["dt_shield_gapL_1"]
    dt_shield_gapL_2 = params["dt_shield_gapL_2"]
    dt_shield_gapL_3 = params["dt_shield_gapL_3"]
    
    # ---- Global parameters ----
    tBOX         = 3e-6
    tCLAD        = 2e-6
    metal_w      = 1e-6
    Xext         = 4e-6
    Ytop_margin  = 2e-6
    Ybot_margin  = 2e-6

    # ============================================================
    # Actual segment heights = base + delta
    # ============================================================

    # Left gap shield segments
    t_gapL_1 = t_shield_gapL + dt_shield_gapL_1
    t_gapL_2 = t_shield_gapL + dt_shield_gapL_2
    t_gapL_3 = t_shield_gapL + dt_shield_gapL_3

    # Right gap shield segments
    t_gapR_1 = t_shield_gapR + dt_shield_gapR_1
    t_gapR_2 = t_shield_gapR + dt_shield_gapR_2
    t_gapR_3 = t_shield_gapR + dt_shield_gapR_3

    # ---- Derived positions ----
    y_core_center = tBOX + H/2
    y_core_bottom = tBOX
    y_core_top = tBOX + H

    y_metal_center     = y_core_bottom + metal_t/2
    y_metal_top        = y_core_bottom + metal_t

    y_topshield_center = tBOX + H + t_shield_core/2
    y_metshield_center = y_metal_top + t_shield_metal/2

    # Segment centers in y
    y_gapL_1 = tBOX + t_gapL_1/2
    y_gapL_2 = tBOX + t_gapL_2/2
    y_gapL_3 = tBOX + t_gapL_3/2

    y_gapR_1 = tBOX + t_gapR_1/2
    y_gapR_2 = tBOX + t_gapR_2/2
    y_gapR_3 = tBOX + t_gapR_3/2

    # Segment widths / x locations
    seg_gap  = g/3

    # Left gap segments span x in [-(W/2+g), -(W/2)]
    x_gapL_1 = -(W/2 + g) + seg_gap/2
    x_gapL_2 = x_gapL_1 + seg_gap
    x_gapL_3 = x_gapL_2 + seg_gap

    # Right gap segments span x in [W/2, W/2+g]
    x_gapR_1 =  (W/2) + seg_gap/2
    x_gapR_2 =  x_gapR_1 + seg_gap
    x_gapR_3 =  x_gapR_2 + seg_gap

    y_span_SiO2 = tBOX + H + t_shield_core + tCLAD + Ytop_margin + Ybot_margin
    y_SiO2_center = -Ybot_margin + y_span_SiO2/2

    x_metal_L  = -(W/2 + g + metal_w/2)
    x_metal_R  = (W/2 + g + metal_w/2)

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
    # SRN Core mask
    # -----------------------------------------------------------
    core_mask = (
        (np.abs(lum["x_m"]) <= W/2) &
        (lum["y_m"] >= y_core_bottom) &
        (lum["y_m"] <= y_core_top)
    )

    # -----------------------------------------------------------
    # Segmented side shield masks (matches segmented LSF geometry)
    # -----------------------------------------------------------

    # segment x-edges
    x_gapL_1_min = -(W/2 + g)
    x_gapL_1_max = x_gapL_1_min + seg_gap

    x_gapL_2_min = x_gapL_1_max
    x_gapL_2_max = x_gapL_2_min + seg_gap

    x_gapL_3_min = x_gapL_2_max
    x_gapL_3_max = -(W/2)

    x_gapR_1_min = W/2
    x_gapR_1_max = x_gapR_1_min + seg_gap

    x_gapR_2_min = x_gapR_1_max
    x_gapR_2_max = x_gapR_2_min + seg_gap

    x_gapR_3_min = x_gapR_2_max
    x_gapR_3_max = W/2 + g

    # left segments
    left_seg1 = (
        (lum["x_m"] >= x_gapL_1_min) &
        (lum["x_m"] <= x_gapL_1_max) &
        (lum["y_m"] >= tBOX) &
        (lum["y_m"] <= tBOX + t_gapL_1)
    )

    left_seg2 = (
        (lum["x_m"] >= x_gapL_2_min) &
        (lum["x_m"] <= x_gapL_2_max) &
        (lum["y_m"] >= tBOX) &
        (lum["y_m"] <= tBOX + t_gapL_2)
    )

    left_seg3 = (
        (lum["x_m"] >= x_gapL_3_min) &
        (lum["x_m"] <= x_gapL_3_max) &
        (lum["y_m"] >= tBOX) &
        (lum["y_m"] <= tBOX + t_gapL_3)
    )

    # right segments
    right_seg1 = (
        (lum["x_m"] >= x_gapR_1_min) &
        (lum["x_m"] <= x_gapR_1_max) &
        (lum["y_m"] >= tBOX) &
        (lum["y_m"] <= tBOX + t_gapR_1)
    )

    right_seg2 = (
        (lum["x_m"] >= x_gapR_2_min) &
        (lum["x_m"] <= x_gapR_2_max) &
        (lum["y_m"] >= tBOX) &
        (lum["y_m"] <= tBOX + t_gapR_2)
    )

    right_seg3 = (
        (lum["x_m"] >= x_gapR_3_min) &
        (lum["x_m"] <= x_gapR_3_max) &
        (lum["y_m"] >= tBOX) &
        (lum["y_m"] <= tBOX + t_gapR_3)
    )

    gap_shield_mask = (
        left_seg1 | left_seg2 | left_seg3 |
        right_seg1 | right_seg2 | right_seg3
    )
    
    # -----------------------------------------------------------
    # HfO2 shield on top of gold electrodes (ALD conformal layer)
    # -----------------------------------------------------------
    top_metal_shield = (
        (
            (lum["x_m"] >= x_metal_L - metal_w/2) &
            (lum["x_m"] <= x_metal_L + metal_w/2)
        ) |
        (
            (lum["x_m"] >= x_metal_R - metal_w/2) &
            (lum["x_m"] <= x_metal_R + metal_w/2)
        )
    ) & (
        (lum["y_m"] >= y_metal_top) &
        (lum["y_m"] <= y_metal_top + t_shield_metal)
    )

    # -----------------------------------------------------------
    # Top shield slab above core mask
    # -----------------------------------------------------------
    top_core_shield = (
        (np.abs(lum["x_m"]) <= W/2) &
        (lum["y_m"] >= y_core_top) &
        (lum["y_m"] <= y_core_top + t_shield_core)
    )

    shield_mask = gap_shield_mask | top_core_shield | top_metal_shield

    # ---------------------------------------------------
    # SiO2 mask (everything that isn't core or shield is SiO2)
    # ---------------------------------------------------
    # SiO2 region = everything that is not SRN or HfO2
    BOX_cladding_mask = ~(core_mask | shield_mask)
    
    # ============================================================
    # DELTA EPSILON MAP
    # ============================================================

    lum["EDCdotEAC"] = lum["EDCx"]*lum["EACx_1V"] + lum["EDCy"]*lum["EACy_1V"]
    E_cross = 2*lum["EDCdotEAC"]

    lum["Deps"] = 0.0
    lum.loc[core_mask, "Deps"] += (3/4) * eps0 * chi3_SRN * E_cross[core_mask]

    # ============================================================
    # EFFECTIVE chi^(2) MAP (EFISH)
    # ============================================================

    # DC field magnitude
    lum["EDC2"] = lum["EDCx"]**2 + lum["EDCy"]**2
    lum["EDC_mag"] = np.sqrt(lum["EDC2"])

    # allocate chi2 map
    lum["chi2_eff"] = 0.0

    # EFISH chi2: (3/2) * chi3 * E_DC
    lum.loc[core_mask, "chi2_eff"] = (
        1.5 * chi3_SRN * lum.loc[core_mask, "EDC_mag"]
    )

    # ============================================================
    # OPTICAL PERMITTIVITY MAP
    # ============================================================

    n_SiO2 = 1.44
    n_HfO2 = 2.1
    n_SRN  = 3.1

    epsr_SiO2 = n_SiO2**2
    epsr_HfO2 = n_HfO2**2
    epsr_SRN  = n_SRN**2

    lum["epsr_opt"] = epsr_SiO2         # default to SiO2 (after all other regions are assigned BOX/Cladding is SiO2)
    lum.loc[shield_mask, "epsr_opt"] = epsr_HfO2       # shields are HfO2
    lum.loc[core_mask, "epsr_opt"] = epsr_SRN       # core is SRN

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
    # MODE-WEIGHTED AVERAGE chi^(2)_eff OVERLAP
    # ============================================================

    Eopt2 = lum["E2"].to_numpy(float)
    chi2  = lum["chi2_eff"].to_numpy(float)

    num_chi2 = np.sum(chi2 * Eopt2) * dA
    den_chi2 = np.sum(Eopt2) * dA

    chi2_eff_avg = num_chi2 / den_chi2

    # ============================================================
    # Vpi L
    # ============================================================

    VpiL_Vm  = lam0 / (2.0 * dneff_per_V)
    VpiL_Vcm = VpiL_Vm * 100
    
    # ============================================================
    # BREAKDOWN FIELD SEARCH (per 1 V applied)
    # ============================================================

    # AC electric field magnitude per volt
    lum["EAC_mag_1V"] = np.sqrt(
        lum["EACx_1V"]**2 + lum["EACy_1V"]**2
    )

    # Maximum field in each material (EAC_mag_1V is still the same as a 1V DC field)
    Emax_SRN  = lum.loc[core_mask, "EAC_mag_1V"].max()
    Emax_HfO2 = lum.loc[shield_mask, "EAC_mag_1V"].max()
    Emax_SiO2 = lum.loc[BOX_cladding_mask, "EAC_mag_1V"].max()
    
    # ============================================================
    # MAXIMUM SAFE VOLTAGE BEFORE BREAKDOWN
    # ============================================================

    Ebreak_SRN  = BREAKDOWN_FIELDS["SRN"]
    Ebreak_HfO2 = BREAKDOWN_FIELDS["HfO2"]
    Ebreak_SiO2 = BREAKDOWN_FIELDS["SiO2"]

    # Voltage that would cause breakdown in each material
    Vbreak_SRN  = Ebreak_SRN  / Emax_SRN
    Vbreak_HfO2 = Ebreak_HfO2 / Emax_HfO2
    Vbreak_SiO2 = Ebreak_SiO2 / Emax_SiO2

    # Device limit
    Vbreak_device = min(Vbreak_SRN, Vbreak_HfO2, Vbreak_SiO2)

    # Identify limiting material
    if Vbreak_device == Vbreak_SRN:
        breakdown_material = "SRN"
    elif Vbreak_device == Vbreak_HfO2:
        breakdown_material = "HfO2"
    else:
        breakdown_material = "SiO2"
    
    # ============================================================
    # Return results
    # ============================================================
    
    return {
        "dneff_per_V": dneff_per_V,
        "chi2_eff_avg_mV": chi2_eff_avg,
        "chi2_eff_avg_pmV": chi2_eff_avg * 1e12,
        "VpiL_Vm": VpiL_Vm,
        "VpiL_Vcm": VpiL_Vcm,
        "lum": lum,
        "core_mask": core_mask,
        "shield_mask": shield_mask,
        "Vbreak_device": Vbreak_device,
        "breakdown_material": breakdown_material
    }