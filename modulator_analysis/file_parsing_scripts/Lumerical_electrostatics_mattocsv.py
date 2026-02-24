import os
import glob
import numpy as np
import pandas as pd
import h5py

def convert_lumerical_electrostatics_to_csv(
    Vdc,
    mat_dir="./lumerical/electrostatics",
    out_dir="./modulator_data/lumerical_electrostatics",
):
    """
    Convert Lumerical electrostatics MAT files to CSV.

    Parameters
    ----------
    Vdc : float
        DC bias voltage used in the Lumerical electrostatics solve (Volts).
    mat_dir : str
        Directory containing Lumerical electrostatics .mat files.
    out_dir : str
        Output directory for CSV files.

    Outputs
    -------
    CSV files with columns:
        x_m, y_m, EDCx, EDCy, EACx_1V, EACy_1V
    """

    os.makedirs(out_dir, exist_ok=True)

    mat_files = sorted(glob.glob(os.path.join(mat_dir, "*.mat")))
    if not mat_files:
        raise FileNotFoundError(f"No electrostatics MAT files found in {mat_dir}")

    print(f"Converting electrostatics fields using Vdc = {Vdc:.3f} V")

    for fpath in mat_files:
        with h5py.File(fpath, "r") as f:
            # Lumerical electrostatics outputs
            E = np.array(f["E"])          # shape (3, N)
            verts = np.array(f["vertices"])  # shape (3, N)

        # --------------------------------------------
        # Unpack 2D electrostatics fields
        # --------------------------------------------

        Ex_DC = E[0, :]   # V/m
        Ey_DC = E[1, :]   # V/m

        # AC field shape per 1 V (linear scaling)
        Ex_AC_1V = Ex_DC / Vdc
        Ey_AC_1V = Ey_DC / Vdc

        # Coordinates
        x = verts[0, :]
        y = verts[1, :]

        # --------------------------------------------
        # Build dataframe
        # --------------------------------------------

        df = pd.DataFrame({
            "x_m": x,
            "y_m": y,

            # DC electrostatic field
            "EDCx": Ex_DC,
            "EDCy": Ey_DC,

            # AC field per volt (shape function)
            "EACx_1V": Ex_AC_1V,
            "EACy_1V": Ey_AC_1V,
        })

        out_name = os.path.splitext(os.path.basename(fpath))[0] + ".csv"
        out_path = os.path.join(out_dir, out_name)
        df.to_csv(out_path, index=False)

        print("Saved:", out_path)

    print("\nAll electrostatics files converted to CSV.")