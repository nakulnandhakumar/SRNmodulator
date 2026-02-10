import os
import glob
import numpy as np
import pandas as pd
import h5py

# === CHANGE IF NEEDED ===
MAT_DIR = r"./modulator_data/Lumerical_mode/mat"
OUT_DIR = r"./modulator_data/Lumerical_mode/csv"
os.makedirs(OUT_DIR, exist_ok=True)

mat_files = sorted(glob.glob(os.path.join(MAT_DIR, "mode_field_g_*nm.mat")))
if not mat_files:
    raise FileNotFoundError("No MAT files found in folder.")

def read_var(f, name):
    return np.array(f[name]).squeeze()

for fpath in mat_files:
    with h5py.File(fpath, "r") as f:
        print("Reading:", os.path.basename(fpath))
        print("Keys:", list(f.keys()))

        x  = read_var(f, "x")
        y  = read_var(f, "y")
        Ex = read_var(f, "Ex")   # may be void/struct → we will not touch
        Ey = read_var(f, "Ey")
        Ez = read_var(f, "Ez")
        E2 = read_var(f, "E2")   # USE THIS

    # Lumerical grid is Ex[Nx,Ny]
    Nx, Ny = E2.shape
    X, Y = np.meshgrid(x, y, indexing="ij")

    df = pd.DataFrame({
        "x_m": X.ravel(),
        "y_m": Y.ravel(),
        "E2": E2.ravel(),
    })

    out_name = os.path.splitext(os.path.basename(fpath))[0] + ".csv"
    out_path = os.path.join(OUT_DIR, out_name)
    df.to_csv(out_path, index=False)

    print("Saved:", out_path)

print("\nAll files converted to CSV.")
