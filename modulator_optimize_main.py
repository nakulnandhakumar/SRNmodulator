"""
modulator_main.py
-----------------

Entry point for SRN electro-optic modulator optimization.

This script:

1. Opens Lumerical DEVICE + MODE sessions
2. Builds initial geometry
3. Computes baseline performance
4. Runs finite-difference gradient optimization
5. Prints evolution of VpiL and loss

This file does NOT:
- Define physics
- Compute overlap integrals
- Handle interpolation
- Define optimization math

It only orchestrates the pipeline.

Optimization strategy:
- Central finite differences
- Gradient-based descent using scaled parameter updates
- Optional backtracking line search

Intended use:
- Proof-of-concept inverse design
- Small iteration counts (5–20)
- Manual inspection of behavior

Author notes:
- No convergence criteria
- No checkpoint saving
"""

import random

from modulator_analysis.modulator_lumapi import LumericalSession
from modulator_analysis.modulator_evaluate import evaluate_params
from modulator_analysis.modulator_fd_optimization import FDOptimizer
from modulator_analysis.modulator_objective import objective_function
from modulator_optimize_config import PARAMS, OPT_KEYS, OPT_SETTINGS, EXPERIMENT, PARAM_BOUNDS, RANDOM_KEYS

opt_keys = OPT_KEYS.copy()
random_keys = RANDOM_KEYS.copy()

# -------------------- Open Lumerical --------------------
session = LumericalSession()
session.open()

best_J = float("inf")
best_params = None
best_rslt = None

# ============================================================
# RANDOM START LOOP
# ============================================================

for run in range(EXPERIMENT["random_starts"]):

    print("\n=======================================")
    print(f" RANDOM START {run+1}/{EXPERIMENT['random_starts']}")
    print("=======================================")

    # -------------------- Initialize parameters --------------------
    params_i = PARAMS.copy()

    # Randomize optimization variables within bounds
    for k in random_keys:
        lo, hi = PARAM_BOUNDS[k]
        params_i[k] = random.uniform(lo, hi)

    print("Initial parameters:")
    for k in opt_keys:
        print(f"{k} = {params_i[k]*1e9:.2f} nm")
    
    # -------------------- Build geometry --------------------
    session.setup_geometry(params_i)

    # -------------------- Baseline --------------------
    print("\n=== BASELINE ===")
    rslt0 = evaluate_params(session, params_i)

    J0 = objective_function(rslt0)

    print(f"J0 = {J0:.6f}")
    print(f"VpiL = {rslt0['VpiL_1V_Vcm']:.3f} V·cm")
    print(f"loss = {rslt0['loss_dB_per_cm']:.3f} dB/cm")

    # -------------------- Optimizer --------------------
    optimizer = FDOptimizer(
        session=session,
        opt_keys=opt_keys,
        rel=OPT_SETTINGS["rel_fd"],
        abs_min=OPT_SETTINGS["abs_fd_min"],
        alpha_init=OPT_SETTINGS["alpha_init"],
        beta=0.5,
        min_alpha=1e-3,
    )

    print("\n=== OPTIMIZATION LOOP ===")

    prev_rslt = rslt0

    # -------------------- Iterations --------------------
    for it in range(EXPERIMENT["num_iterations"]):

        print(f"\n--- Iteration {it+1} ---")

        params_i, grads = optimizer.step(params_i)
        rslt_i = evaluate_params(session, params_i)
        J_i = objective_function(rslt_i)
        print(f"J = {J_i:.6f}")
        # ---- breakdown voltage info ----
        Vbreak = rslt_i["Vbreak_device"]
        breakdown_material = rslt_i["breakdown_material"]

        bias_fraction = 0.8
        Vbias = bias_fraction * Vbreak

        # VpiL values
        VpiL_Vcm_1V = rslt_i["VpiL_1V_Vcm"]
        VpiL_bias = VpiL_Vcm_1V / Vbias

        print(
            f"VpiL(1V) = {VpiL_Vcm_1V:.3f} V·cm   "
            f"(Δ {VpiL_Vcm_1V - prev_rslt['VpiL_1V_Vcm']:+.3f})"
        )

        print(
            f"VpiL({bias_fraction*100:.0f}% Vbreak) = {VpiL_bias:.3f} V·cm   "
            f"(Vbreak={Vbreak:.1f}V, limit={breakdown_material})"
        )

        print(
            f"loss = {rslt_i['loss_dB_per_cm']:.3f} dB/cm   "
            f"(Δ {rslt_i['loss_dB_per_cm'] - prev_rslt['loss_dB_per_cm']:+.3f})"
        )

        prev_rslt = rslt_i

    # -------------------- Track best result --------------------
    if J_i < best_J:
        best_J = J_i
        best_params = params_i.copy()
        best_rslt = rslt_i.copy()

# ============================================================
# TRUE DEVICE PERFORMANCE AT BREAKDOWN BIAS
# ============================================================

Vbreak = best_rslt["Vbreak_device"]
breakdown_material = best_rslt["breakdown_material"]

# choose safe operating voltage (80% of breakdown)
bias_fraction = 0.8
Vbias = bias_fraction * Vbreak

# VpiL computed at 1 V in overlap code
VpiL_Vcm_1V = best_rslt["VpiL_1V_Vcm"]

# true VpiL when biased at Vbias
VpiL_Vcm_true = VpiL_Vcm_1V / Vbias

print("\n=======================================")
print(" DEVICE PERFORMANCE AT SAFE BIAS")
print("=======================================")

print(f"Breakdown voltage = {Vbreak:.2f} V")
print(f"Limiting material = {breakdown_material}")
print(f"Operating voltage (80%) = {Vbias:.2f} V")

print(f"\nVpiL @ 1V = {VpiL_Vcm_1V:.3f} V·cm")
print(f"True VpiL @ {Vbias:.2f} V = {VpiL_Vcm_true:.3f} V·cm")
print(f"Loss = {best_rslt['loss_dB_per_cm']:.3f} dB/cm")

session.close()