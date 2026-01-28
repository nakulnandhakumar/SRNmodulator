import pandas as pd

comsol_path = r"modulator_data/COMSOL_ACDC_field_dist/COMSOL_HfO2_ALDShield_reducedAu_acdc_field_dist.csv"

# COMSOL export starts comment lines with %
comsol = pd.read_csv(comsol_path, comment="%", header=0)

print(comsol.columns)
print(comsol.head())

comsol = comsol.rename(columns={
    "esAC.Ex (V/m)": "EACx",
    "esAC.Ey (V/m)": "EACy",
    "esDC.Ex (V/m)": "EDCx",
    "esDC.Ey (V/m)": "EDCy",
})

comsol = comsol[["x","y","g","EACx","EACy","EDCx","EDCy"]]

print(comsol.head())

import numpy as np

comsol["EDC2"] = comsol["EDCx"]**2 + comsol["EDCy"]**2
comsol["EAC2"] = comsol["EACx"]**2 + comsol["EACy"]**2
comsol["EDCdotEAC"] = comsol["EDCx"]*comsol["EACx"] + comsol["EDCy"]*comsol["EACy"]

print(comsol[["EDC2","EAC2","EDCdotEAC"]].head())

lum = pd.read_csv("modulator_data/Lumerical_mode_dist/csv/mode_field_g_400nm.csv")

print(lum.columns)
print(lum.head())

g_nm = 400   # change to match the file you loaded
g_m = g_nm * 1e-9

com_g = comsol[np.isclose(comsol["g"], g_m)]

print("COMSOL points for gap:", len(com_g))
print(com_g.head())

from scipy.interpolate import griddata
import numpy as np

pts = np.column_stack((com_g["x"].values, com_g["y"].values))
tgt = np.column_stack((lum["x_m"].values, lum["y_m"].values))

lum["EDC2"] = griddata(pts, com_g["EDC2"].values, tgt, method="linear")
lum["EAC2"] = griddata(pts, com_g["EAC2"].values, tgt, method="linear")
lum["EDCdotEAC"] = griddata(pts, com_g["EDCdotEAC"].values, tgt, method="linear")

print("NaN fraction EDC2:", np.isnan(lum["EDC2"]).mean())
print("NaN fraction EAC2:", np.isnan(lum["EAC2"]).mean())
print("NaN fraction dot :", np.isnan(lum["EDCdotEAC"]).mean())

print(lum.columns)

W = 0.450e-6
tBOX = 3e-6
H = 0.350e-6

y_core_bot = tBOX
y_core_top = tBOX + H

core_mask = (
    (np.abs(lum["x_m"]) <= W/2) &
    (lum["y_m"] >= y_core_bot) &
    (lum["y_m"] <= y_core_top)
)

print("Core mask fraction:", core_mask.mean())