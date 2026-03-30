from modulator_analysis.modulator_lumapi import LumericalSession
from modulator_analysis.modulator_evaluate import evaluate_params
from modulator_analysis.modulator_fd_optimization import FDOptimizer
from modulator_analysis.modulator_objective import objective_function
from config import PARAMS

# Define loop over gap values
gap_values = [400e-9, 450e-9, 500e-9, 550e-9, 600e-9, 650e-9, 700e-9, 750e-9, 800e-9, 850e-9, 900e-9, 950e-9, 1000e-9]
true_VpiL_results = {}
loss_results = {}

for g in gap_values:
    print(f"\n=== Evaluating gap g = {g*1e9:.0f} nm ===")

    # Update gap in parameters
    params = PARAMS.copy()
    params["g"] = g
    params["t_shield_gapR"] = 0.5 * g
    params["t_shield_gapL"] = 0.5 * g
    params["t_shield_core"] = 0.5 * g
    params["t_shield_metal"] = 0.5 * g

    # Open Lumerical session and setup geometry
    session = LumericalSession()
    session.open()
    session.setup_geometry(params)

    # Evaluate performance
    results = evaluate_params(session, params)

    # Find breakdown VpiL at 1V bias
    Vbreak = results["Vbreak_device"]
    breakdown_material = results["breakdown_material"]

    # choose safe operating voltage (80% of breakdown)
    bias_fraction = 0.8
    Vbias = bias_fraction * Vbreak

    # VpiL computed at 1 V in overlap code
    VpiL_1V = results["VpiL_Vcm"]

    # true VpiL when biased at Vbias
    VpiL_true = VpiL_1V / Vbias
    
    print(
        f"gap = {g*1e9:.0f} nm: VpiL(1V) = {VpiL_1V:.3f} V·cm, "
        f"Vbreak = {Vbreak:.1f} V ({breakdown_material}), "
        f"Vbias = {Vbias:.1f} V, "
        f"VpiL(true) = {VpiL_true:.3f} V·cm, "
        f"loss = {results['loss_dB_per_cm']:.3f} dB/cm"
    )
    
    true_VpiL_results[g] = VpiL_true
    loss_results[g] = results["loss_dB_per_cm"]
    