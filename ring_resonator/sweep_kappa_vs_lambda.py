import numpy as np
import csv
import matplotlib.pyplot as plt
import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]

def sweep_kappa_vs_lambda(
    g_opt,
    lambda_start,
    lambda_end,
    Npoints,
    lsf_path=r"./lumerical/mode/ring_supermode.lsf",
    project_path=r"./lumerical/mode/modulator_mode.lms",
    output_csv="kappa_vs_lambda.csv",
    hide=False
):
    """
    Sweep wavelength in Lumerical MODE to extract kappa_prime, neff_even, neff_odd.

    Parameters:
        g_opt (float): optimal coupling gap (meters)
        lambda_start (float): start wavelength (meters)
        lambda_end (float): end wavelength (meters)
        Npoints (int): number of wavelength points
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
    # WAVELENGTH SWEEP
    # ============================================================
    lambdas = np.linspace(lambda_start, lambda_end, Npoints)

    kappa_prime_list = []
    neff_even_list = []
    neff_odd_list = []

    for lam in lambdas:
        print(f"Running λ = {lam*1e9:.2f} nm")

        # send variables
        mode.putv("g", g_opt)
        mode.putv("lambda", lam)

        # run simulation
        mode.eval(lsf_script)

        # extract results
        kappa_prime = mode.getv("kappa_prime")
        neff_even = mode.getv("neff_even")
        neff_odd  = mode.getv("neff_odd")

        kappa_prime_list.append(kappa_prime)
        neff_even_list.append(neff_even)
        neff_odd_list.append(neff_odd)

    # ============================================================
    # CONVERT TO ARRAYS
    # ============================================================
    lambdas = np.array(lambdas)
    kappa_prime_array = np.array(kappa_prime_list)
    neff_even_array = np.array(neff_even_list)
    neff_odd_array = np.array(neff_odd_list)

    # ============================================================
    # SAVE TO CSV
    # ============================================================
    with open(output_csv, mode="w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "lambda (m)",
            "lambda (nm)",
            "kappa_prime (1/m)",
            "neff_even",
            "neff_odd"
        ])

        for i in range(len(lambdas)):
            writer.writerow([
                lambdas[i],
                lambdas[i]*1e9,
                kappa_prime_array[i],
                neff_even_array[i],
                neff_odd_array[i]
            ])

    print(f"\nSaved data to {output_csv}")

    # ============================================================
    # RETURN DATA (VERY USEFUL)
    # ============================================================
    return {
        "lambda": lambdas,
        "kappa_prime": kappa_prime_array,
        "neff_even": neff_even_array,
        "neff_odd": neff_odd_array
    }
    
data = sweep_kappa_vs_lambda(
    g_opt=467.80e-9,
    lambda_start=1.54e-6,
    lambda_end=1.56e-6,
    Npoints=100,
    lsf_path=r"./lumerical/mode/ring_supermode.lsf",
    project_path=r"./lumerical/mode/ring_supermode.lms",
    output_csv="kappa_vs_lambda.csv",
    hide=False
)