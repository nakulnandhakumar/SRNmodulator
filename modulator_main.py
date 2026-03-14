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
from config import PARAMS, OPT_KEYS, OPT_SETTINGS, EXPERIMENT, PARAM_BOUNDS

opt_keys = OPT_KEYS.copy()

# -------------------- Open Lumerical --------------------
session = LumericalSession()
session.open()

best_J = float("inf")
best_params = None

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
    for k in opt_keys:
        lo, hi = PARAM_BOUNDS[k]
        params_i[k] = random.uniform(lo, hi)

    print("Initial parameters:")
    for k in opt_keys:
        print(f"{k} = {params_i[k]*1e9:.2f} nm")
    
    # -------------------- Build geometry --------------------
    session.setup_geometry(params_i)

    # -------------------- Baseline --------------------
    print("\n=== BASELINE ===")
    res0 = evaluate_params(session, params_i)

    J0 = objective_function(res0)

    print(f"J0 = {J0:.6f}")
    print(f"VpiL = {res0['VpiL_Vcm']:.3f} V·cm")
    print(f"loss = {res0['loss_dB_per_cm']:.3f} dB/cm")

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

    prev_res = res0

    # -------------------- Iterations --------------------
    for it in range(EXPERIMENT["num_iterations"]):

        print(f"\n--- Iteration {it+1} ---")

        params_i, grads = optimizer.step(params_i)
        res_i = evaluate_params(session, params_i)
        J_i = objective_function(res_i)

        print(f"J = {J_i:.6f}")
        print(f"VpiL = {res_i['VpiL_Vcm']:.3f} V·cm   (Δ {res_i['VpiL_Vcm'] - prev_res['VpiL_Vcm']:+.3f})")
        print(f"loss = {res_i['loss_dB_per_cm']:.3f} dB/cm   (Δ {res_i['loss_dB_per_cm'] - prev_res['loss_dB_per_cm']:+.3f})")

        prev_res = res_i

    # -------------------- Track best result --------------------
    if J_i < best_J:
        best_J = J_i
        best_params = params_i.copy()

# ============================================================
# FINAL RESULT
# ============================================================

print("\n=======================================")
print(" BEST RESULT ACROSS RANDOM STARTS")
print("=======================================")

print(f"Best objective J = {best_J:.6f}")
print("Best parameters:")

for k, v in best_params.items():
    print(f"{k} = {v:.3e}")

session.close()