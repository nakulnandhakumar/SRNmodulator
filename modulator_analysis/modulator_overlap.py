import numpy as np
import pandas as pd
from scipy.interpolate import griddata

# ============================================================
# FILE PATHS
# ============================================================

COMSOL_PATH = r"modulator_data/COMSOL_ACDC_field_dist/COMSOL_HfO2_ALDShield_reducedAu_acdc_field_dist.csv"
LUM_PATH    = r"modulator_data/Lumerical_mode_dist/csv/mode_field_g_300nm.csv"

# ============================================================
# USER SETTINGS
# ============================================================

g_nm = 300
g_m  = g_nm * 1e-9

lam0 = 1.55e-6
eps0 = 8.854e-12

chi3_SRN = 6e-19   # m^2 / V^2  (update if you refine this)

# ============================================================
# GEOMETRY PARAMETERS (meters)
# ============================================================

W      = 0.450e-6
H      = 0.350e-6
tBOX   = 3e-6
tCLAD  = 2e-6
metal_t = 100e-9

t_shield_top = 0.5 * g_m

y_core_bot = tBOX
y_core_top = tBOX + H

# ============================================================
# LOAD COMSOL DATA
# ============================================================

comsol = pd.read_csv(COMSOL_PATH, comment="%", header=0)

comsol = comsol.rename(columns={
    "esAC.Ex (V/m)": "EACx",
    "esAC.Ey (V/m)": "EACy",
    "esDC.Ex (V/m)": "EDCx",
    "esDC.Ey (V/m)": "EDCy",
})

comsol = comsol[["x", "y", "g", "EACx", "EACy", "EDCx", "EDCy"]]

# electrostatic invariants
comsol["EDC2"]       = comsol["EDCx"]**2 + comsol["EDCy"]**2
comsol["EAC2"]       = comsol["EACx"]**2 + comsol["EACy"]**2
comsol["EDCdotEAC"]  = comsol["EDCx"]*comsol["EACx"] + comsol["EDCy"]*comsol["EACy"]

# select this gap
com_g = comsol[np.isclose(comsol["g"], g_m)]
print("COMSOL points for gap:", len(com_g))

# ============================================================
# LOAD LUMERICAL MODE DATA
# ============================================================

lum = pd.read_csv(LUM_PATH)

if "E2" not in lum.columns:
    raise ValueError("Expected column 'E2' in Lumerical CSV.")

# ============================================================
# INTERPOLATE COMSOL → LUMERICAL GRID
# ============================================================

pts = np.column_stack((com_g["x"].values, com_g["y"].values))
tgt = np.column_stack((lum["x_m"].values, lum["y_m"].values))

lum["EDC2"]      = griddata(pts, com_g["EDC2"].values,      tgt, method="linear")
lum["EAC2"]      = griddata(pts, com_g["EAC2"].values,      tgt, method="linear")
lum["EDCdotEAC"] = griddata(pts, com_g["EDCdotEAC"].values, tgt, method="linear")

print("NaN fraction:",
      np.isnan(lum["EDC2"]).mean(),
      np.isnan(lum["EAC2"]).mean(),
      np.isnan(lum["EDCdotEAC"]).mean())

# ============================================================
# REGION MASKS
# ============================================================

core_mask = (
    (np.abs(lum["x_m"]) <= W/2) &
    (lum["y_m"] >= y_core_bot) &
    (lum["y_m"] <= y_core_top)
)

left_gap_hf02 = (
    (lum["x_m"] >= -(W/2 + g_m)) &
    (lum["x_m"] <= -(W/2)) &
    (lum["y_m"] >= y_core_bot) &
    (lum["y_m"] <= y_core_top)
)

right_gap_hf02 = (
    (lum["x_m"] >=  (W/2)) &
    (lum["x_m"] <=  (W/2 + g_m)) &
    (lum["y_m"] >= y_core_bot) &
    (lum["y_m"] <= y_core_top)
)

gap_hf02_mask = left_gap_hf02 | right_gap_hf02

top_core_hf02_mask = (
    (np.abs(lum["x_m"]) <= W/2) &
    (lum["y_m"] >= y_core_top) &
    (lum["y_m"] <= y_core_top + t_shield_top)
)

hf02_mask = gap_hf02_mask | top_core_hf02_mask

print("Core frac:", core_mask.mean())
print("HfO2 frac:", hf02_mask.mean())

# ============================================================
# DELTA EPSILON MAP (KERR)
# ============================================================

E_nl = 2*lum["EDCdotEAC"] + lum["EAC2"]

lum["Deps"] = 0.0
lum.loc[core_mask, "Deps"] += (3/4) * eps0 * chi3_SRN * E_nl[core_mask]

print("Δε stats:\n", lum["Deps"].describe())

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
# OVERLAP INTEGRALS
# ============================================================

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
# Vpi L
# ============================================================

VpiL_SI  = lam0 / (2.0 * dneff_per_V)
VpiL_Vcm = VpiL_SI * 100

print("Vπ·L (V·m) :", VpiL_SI)
print("Vπ·L (V·cm):", VpiL_Vcm)