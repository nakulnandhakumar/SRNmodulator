import numpy as np
import pandas as pd
from scipy.interpolate import griddata


def compute_modulator_overlap(g_nm):
    """
    Compute Δn_eff, χ²_eff, and Vπ·L for a given gap g (nm).

    Parameters
    ----------
    g_nm : float
        Gap width in nanometers.

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
    W            = 0.450e-6;    # SRN core width
    H            = 0.350e-6;    # SRN core height 
    g            = g_nm * 1e-9;    # electrode–sidewall gap 
    tBOX         = 3e-6;      # BOX thickness below core
    tCLAD        = 2e-6;      # top cladding thickness
    metal_w      = 1e-6;      # metal electrode width
    metal_t      = 0.100e-6;    # metal electrode height
    Xext         = 4e-6;     # half-width of simulation window
    Ytop_margin  = 2e-6;     # extra margin above cladding
    Ybot_margin  = 2e-6;     # extra margin below BOX

    t_shield_top = 0.5*g;     # top shield thickness

    # ---- Derived positions ----
    y_core_center         = tBOX + H/2
    y_topshield_center    = tBOX + H + t_shield_top/2
    y_sideshield_center = tBOX + t_shield_top/2

    y_span_SiO2 = tBOX + H + metal_t + t_shield_top + tCLAD + Ytop_margin + Ybot_margin
    y_SiO2_center = -Ybot_margin + y_span_SiO2/2

    x_shield_L = -(W/2 + g/2)
    x_shield_R = (W/2 + g/2)

    x_metal_L  = -(W/2 + g + metal_w/2)
    x_metal_R  = (W/2 + g + metal_w/2)

    y_core_bottom      = tBOX
    y_core_top         = tBOX + H
    y_metal_center     = y_core_bottom + metal_t/2
    y_metal_top        = y_core_bottom + metal_t

    y_metshield_center = y_metal_top + t_shield_top/2
    
    # ---- Core/Shield Taper parameters ----
    g_bottom = g        # width at bottom of shield
    g_top_thickness    = 0.3*g    # width at top from the electrode

    ftaper = 0.5
    y0 = y_sideshield_center - t_shield_top/2
    y1 = y_sideshield_center + t_shield_top/2
    y_taper = y0 + ftaper*(y1 - y0)
    
    # Left shield (core-facing taper)
    xL_outer = -(W/2 + g)        # fixed outer edge
    xL_inner_bot = -W/2          # inner edge at bottom
    xL_inner_top = -(W/2 + (g_bottom - g_top_thickness))  # inner edge moves toward core
    
    # Right shield (core-facing taper)
    xR_outer =  (W/2 + g)        # fixed outer edge
    xR_inner_bot =  W/2          # inner edge at bottom
    xR_inner_top =  W/2 + (g_bottom - g_top_thickness)  # inner edge moves toward core

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
    # Side shield masks (tapered poly, matches LSF)
    # -----------------------------------------------------------
    x = lum["x_m"].values
    y = lum["y_m"].values

    # side shield vertical extent (matches LSF, NOT core height)
    yside = (y >= y0) & (y <= y1)

    # piecewise inner wall x-position vs y
    # Left
    x_inner_left = np.where(
        y <= y_taper,
        xL_inner_bot,
        xL_inner_bot + (xL_inner_top - xL_inner_bot) * (y - y_taper) / (y1 - y_taper)
    )

    # Right
    x_inner_right = np.where(
        y <= y_taper,
        xR_inner_bot,
        xR_inner_bot + (xR_inner_top - xR_inner_bot) * (y - y_taper) / (y1 - y_taper)
    )

    left_shield_mask = (
        yside &
        (x >= xL_outer) &
        (x <= x_inner_left)
    )

    right_shield_mask = (
        yside &
        (x <= xR_outer) &
        (x >= x_inner_right)
    )

    gap_hf02_mask = left_shield_mask | right_shield_mask

    # -----------------------------------------------------------
    # Top shield slab above core mask
    # -----------------------------------------------------------
    top_core_hf02_mask = (
        (np.abs(lum["x_m"]) <= W/2) &
        (lum["y_m"] >= y_core_top) &
        (lum["y_m"] <= y_core_top + t_shield_top)
    )

    hf02_mask = gap_hf02_mask | top_core_hf02_mask

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

    lum["epsr_opt"] = epsr_SiO2
    lum.loc[hf02_mask, "epsr_opt"] = epsr_HfO2
    lum.loc[core_mask, "epsr_opt"] = epsr_SRN

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

    print(f"dA = {dA:.3e} m^2")

    num = np.sum(deps * w) * dA
    den = 2 * np.sum(eps0 * epsr * w) * dA

    dneff_per_V = num / den

    print("Δn_eff / V =", dneff_per_V)

    # ============================================================
    # MODE-WEIGHTED AVERAGE chi^(2)_eff OVERLAP
    # ============================================================

    Eopt2 = lum["E2"].to_numpy(float)
    chi2  = lum["chi2_eff"].to_numpy(float)

    num_chi2 = np.sum(chi2 * Eopt2) * dA
    den_chi2 = np.sum(Eopt2) * dA

    chi2_eff_avg = num_chi2 / den_chi2

    print("Mode-weighted χ²_eff (m/V)=", chi2_eff_avg, "m/V")
    print("Mode-weighted χ²_eff (pm/V) =", chi2_eff_avg * 1e12, "pm/V")

    # ============================================================
    # Vpi L
    # ============================================================

    VpiL_Vm  = lam0 / (2.0 * dneff_per_V)
    VpiL_Vcm = VpiL_Vm * 100

    print("Vπ·L (V·m) :", VpiL_Vm)
    print("Vπ·L (V·cm):", VpiL_Vcm)
    
    return {
        "g_nm": g_nm,
        "dneff_per_V": dneff_per_V,
        "chi2_eff_avg_mV": chi2_eff_avg,
        "chi2_eff_avg_pmV": chi2_eff_avg * 1e12,
        "VpiL_Vm": VpiL_Vm,
        "VpiL_Vcm": VpiL_Vcm,
        "lum": lum,
    }