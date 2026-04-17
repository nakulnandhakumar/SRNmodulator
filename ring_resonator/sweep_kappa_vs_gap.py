import numpy as np
import csv
import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi  # pyright: ignore[reportMissingImports]


def sweep_kappa_vs_gap(
    lambda0,
    gap_start,
    gap_end,
    Npoints,
    lsf_path=r"./lumerical/mode/ring_supermode.lsf",
    project_path=r"./lumerical/mode/modulator_mode.lms",
    output_csv="kappa_vs_gap.csv",
    hide=False
):
    """
    Sweep coupling gap in Lumerical MODE to extract kappa_prime.

    Parameters:
        lambda0 (float): wavelength (meters)
        gap_start (float): starting gap (meters)
        gap_end (float): ending gap (meters)
        Npoints (int): number of gap points
        lsf_path (str): path to LSF script
        project_path (str): path to MODE project file
        output_csv (str): output CSV filename
        hide (bool): run Lumerical in background if True

    Returns:
        dict with arrays
    """

    # ============================================================
    # CREATE SESSION
    # ============================================================
    mode = lumapi.MODE(hide=hide, project=project_path)

    with open(lsf_path) as f:
        lsf_script = f.read()

    # ============================================================
    # GAP SWEEP
    # ============================================================
    gaps = np.linspace(gap_start, gap_end, Npoints)

    kappa_prime_list = []

    for g in gaps:
        print(f"Running gap = {g*1e9:.2f} nm")

        # send variables
        mode.putv("g", g)
        mode.putv("lambda", lambda0)

        # run simulation
        mode.eval(lsf_script)

        # extract result
        kappa_prime = mode.getv("kappa_prime")
        kappa_prime_list.append(kappa_prime)

    # ============================================================
    # CONVERT TO ARRAYS
    # ============================================================
    gaps = np.array(gaps)
    kappa_prime_array = np.array(kappa_prime_list)

    # ============================================================
    # SAVE TO CSV
    # ============================================================
    with open(output_csv, mode="w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "gap (m)",
            "gap (nm)",
            "kappa_prime (1/m)"
        ])

        for i in range(len(gaps)):
            writer.writerow([
                gaps[i],
                gaps[i] * 1e9,
                kappa_prime_array[i]
            ])

    print(f"\nSaved data to {output_csv}")

    # ============================================================
    # RETURN DATA
    # ============================================================
    return {
        "gap": gaps,
        "kappa_prime": kappa_prime_array
    }


# ============================================================
# EXAMPLE USAGE
# ============================================================
# data = sweep_kappa_vs_gap(
#     lambda0=1.55e-6,
#     gap_start=320e-9,
#     gap_end=330e-9,
#     Npoints=20,
#     lsf_path=r"./lumerical/mode/ring_supermode.lsf",
#     project_path=r"./lumerical/mode/modulator_mode.lms",
#     output_csv="kappa_vs_gap.csv",
#     hide=False
# )