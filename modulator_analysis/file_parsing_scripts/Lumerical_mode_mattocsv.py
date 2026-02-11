import os
import glob
import numpy as np
import pandas as pd
import h5py

def convert_lumerical_mode_to_csv(
    mat_dir="./modulator_data/lumerical_mode/mat",
    out_dir="./modulator_data/lumerical_mode/csv",
):
    """
    Convert Lumerical MODE solver MAT files to CSV.

    Parameters
    ----------
    mat_dir : str
        Directory containing Lumerical mode .mat files.
    out_dir : str
        Output directory for CSV files.
    file_pattern : str
        Glob pattern for selecting mode MAT files.

    Outputs
    -------
    CSV files with columns:
        x_m, y_m, E2

    Notes
    -----
    - Uses |E|^2 (E2) directly for overlap integrals
    - Coordinates are flattened onto the optical grid
    """

    os.makedirs(out_dir, exist_ok=True)

    mat_files = sorted(glob.glob(os.path.join(mat_dir, "*.mat")))
    if not mat_files:
        raise FileNotFoundError(f"No mode MAT files found in {mat_dir}")

    def read_var(f, name):
        return np.array(f[name]).squeeze()

    for fpath in mat_files:
        with h5py.File(fpath, "r") as f:
            print("\nReading:", os.path.basename(fpath))
            print("Keys:", list(f.keys()))

            x  = read_var(f, "x")
            y  = read_var(f, "y")
            E2 = read_var(f, "E2")   # |E|^2 on (Nx, Ny) grid

        # Build grid
        X, Y = np.meshgrid(x, y, indexing="ij")

        # Flatten into dataframe
        df = pd.DataFrame({
            "x_m": X.ravel(),
            "y_m": Y.ravel(),
            "E2":  E2.ravel(),
        })

        out_name = os.path.splitext(os.path.basename(fpath))[0] + ".csv"
        out_path = os.path.join(out_dir, out_name)
        df.to_csv(out_path, index=False)

        print("Saved:", out_path)

    print("\nAll mode-field files converted to CSV.")