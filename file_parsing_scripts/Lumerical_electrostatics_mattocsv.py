import os
import glob
import numpy as np
import pandas as pd
import h5py

# ============================================================
# USER SETTINGS
# ============================================================

V_DC = 100.0   # volts used in Lumerical electrostatics solve

# ============================================================
# PATHS
# ============================================================

MAT_DIR = r"./modulator_data/Lumerical_electrostatics/mat"
OUT_DIR = r"./modulator_data/Lumerical_electrostatics/csv"
os.makedirs(OUT_DIR, exist_ok=True)

mat_files = sorted(glob.glob(os.path.join(MAT_DIR, "*.mat")))
if not mat_files:
    raise FileNotFoundError("No electrostatics MAT files found.")

# ============================================================
# CONVERSION
# ============================================================

for fpath in mat_files:
    with h5py.File(fpath, "r") as f:
        print("\nReading:", os.path.basename(fpath))
        print("Keys:", list(f.keys()))

        E     = np.array(f["E"])         # shape (3, N)
        verts = np.array(f["vertices"])  # shape (3, N)

    # --------------------------------------------------------
    # Unpack fields (2D electrostatics → Ex, Ey only)
    # --------------------------------------------------------

    Ex_DC = E[0, :]   # V/m
    Ey_DC = E[1, :]   # V/m

    # AC shape field per 1 V
    Ex_AC_1V = Ex_DC / V_DC
    Ey_AC_1V = Ey_DC / V_DC

    # Coordinates
    x = verts[0, :]
    y = verts[1, :]

    # --------------------------------------------------------
    # Build dataframe
    # --------------------------------------------------------

    df = pd.DataFrame({
        "x_m": x,
        "y_m": y,

        # DC bias field
        "EDCx": Ex_DC,
        "EDCy": Ey_DC,

        # AC field per volt
        "EACx_1V": Ex_AC_1V,
        "EACy_1V": Ey_AC_1V,
    })

    out_name = os.path.splitext(os.path.basename(fpath))[0] + ".csv"
    out_path = os.path.join(OUT_DIR, out_name)
    df.to_csv(out_path, index=False)

    print("Saved:", out_path)

print("\nAll electrostatics files converted to CSV.")