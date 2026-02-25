from modulator_analysis.modulator_lumapi import LumericalSession
from modulator_analysis.modulator_evaluate import evaluate_params
from modulator_analysis.modulator_fd_optimization import FDOptimizer
from modulator_analysis.modulator_objective import objective_function

# ------------------- Parameters to set from Python script --------------
# g            = set from python script;    # electrode–sidewall gap
# Vdc          = 100.0V;                    # applied voltage for electrostatics (keep fixed)
# W            = 450nm;                     # SRN core width (keep fixed for now)
# H            = 350nm;                     # SRN core height (keep fixed for now)
# metal_t      = 100nm;                     # metal electrode thickness (height) (keep fixed for now)
# t_shield_gapR = set from python script;    # thickness of the shield within the right gap
# t_shield_gapL = set from python script;    # thickness of the shield within
# t_shield_core = set from python script;   # thickness of the shield above the core
# t_shield_metal = set from python script;  # thickness of the shield above the metal electrodes
# -----------------------------------------------------------------------

# -------------------- Initial parameters --------------------
params = {
    "g": 600e-9,
    "Vdc": 100.0,
    "W": 450e-9,
    "H": 350e-9,
    "metal_t": 100e-9,
    "t_shield_gapR": 0.5 * 600e-9,
    "t_shield_gapL": 0.5 * 600e-9,
    "t_shield_core": 0.5 * 600e-9,
    "t_shield_metal": 0.5 * 600e-9,
}

OPT_KEYS = [
    "g",
    "t_shield_gapR",
    "t_shield_gapL",
    "t_shield_core",
]

weights = {
    "VpiL": 1.0,
    "loss": 0.3,   # modest loss weight (good for demo)
}

# -------------------- Open Lumerical --------------------
session = LumericalSession()
session.open()
session.setup_geometry(params)

# -------------------- Baseline --------------------
print("\n=== BASELINE ===")
res0 = evaluate_params(session, params)

refs = {
    "VpiL_Vcm": res0["VpiL_Vcm"],
    "loss_dB_per_cm": res0["loss_dB_per_cm"],
}

J0 = objective_function(res0, refs, weights)

print(f"J0 = {J0:.6f}")
print(f"VpiL = {res0['VpiL_Vcm']:.3f} V·cm")
print(f"loss = {res0['loss_dB_per_cm']:.3f} dB/cm")

# -------------------- Optimizer --------------------
optimizer = FDOptimizer(
    session=session,
    refs=refs,
    opt_keys=OPT_KEYS,
    weights=weights,
    rel=0.03,          # FD perturbation (~3%)
    step_frac=0.005,   # small step (0.5%)
)

# -------------------- Optimization loop --------------------
print("\n=== OPTIMIZATION LOOP ===")

params_i = params
prev_res = res0

for it in range(5):
    print(f"\n--- Iteration {it+1} ---")

    params_i, grads = optimizer.step(params_i)
    res_i = evaluate_params(session, params_i)
    J_i = objective_function(res_i, refs, weights)

    print(f"J = {J_i:.6f}")
    print(f"VpiL = {res_i['VpiL_Vcm']:.3f} V·cm   (Δ {res_i['VpiL_Vcm'] - prev_res['VpiL_Vcm']:+.3f})")
    print(f"loss = {res_i['loss_dB_per_cm']:.3f} dB/cm   (Δ {res_i['loss_dB_per_cm'] - prev_res['loss_dB_per_cm']:+.3f})")

    prev_res = res_i

session.close()