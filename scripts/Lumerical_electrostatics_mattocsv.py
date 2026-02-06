import os
import glob
import numpy as np
import pandas as pd
import h5py

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

    # --- unpack ---
    Ex = E[0, :]
    Ey = E[1, :]

    x = verts[0, :]
    y = verts[1, :]

    Enorm = np.sqrt(Ex**2 + Ey**2)

    # --- dataframe ---
    df = pd.DataFrame({
        "x_m": x,
        "y_m": y,
        "Ex": Ex,
        "Ey": Ey,
        "E_norm": Enorm,
    })

    out_name = os.path.splitext(os.path.basename(fpath))[0] + ".csv"
    out_path = os.path.join(OUT_DIR, out_name)
    df.to_csv(out_path, index=False)

    print("Saved:", out_path)

print("\nAll electrostatics files converted to CSV.")