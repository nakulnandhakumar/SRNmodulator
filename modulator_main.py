from modulator_analysis.modulator_lumapi import LumericalSession
from modulator_analysis.modulator_evaluate import evaluate_params
from modulator_analysis.modulator_fd_optimization import compute_fd_gradient, update_params
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

g = 700e-9            # electrode–sidewall gap in meters
Vdc = 100.0              # DC voltage applied to electrode in V
W = 450e-9               # SRN core width in meters
H = 350e-9               # SRN core height in meters
metal_t = 100e-9         # metal electrode thickness (height) in meters
t_shield_gapR = 0.5*g     # thickness of the shield within the right gap in meters
t_shield_gapL = 0.5*g    # thickness of the shield within the left gap in meters
t_shield_core = 0.5*g    # thickness of the shield above the core in meters
t_shield_metal = 0.5*g   # thickness of the shield above the metal electrodes in meters

params = {
    "g": g,
    "Vdc": Vdc,
    "W": W,
    "H": H,
    "metal_t": metal_t,
    "t_shield_gapR": t_shield_gapR,
    "t_shield_gapL": t_shield_gapL,
    "t_shield_core": t_shield_core,
    "t_shield_metal": t_shield_metal
}

OPT_KEYS = [
    "g",
    "t_shield_gapR",
    "t_shield_gapL",
    "t_shield_core",
]

weights = {
    "VpiL": 1.0,
    "loss": 0.0,
}

session = LumericalSession()
session.open()
session.setup_geometry(params)

print("\n=== BASELINE ===")
res0 = evaluate_params(session, params)
refs = {
    "VpiL_Vcm": res0["VpiL_Vcm"],
    "loss_dB_per_cm": res0["loss_dB_per_cm"]
}
J0 = objective_function(res0, refs, weights)
print("J0 =", J0)
print("VpiL_Vcm =", res0["VpiL_Vcm"])
print("loss_dB_per_cm =", res0["loss_dB_per_cm"])

print("\n=== FD GRADIENT ===")
grads = compute_fd_gradient(session, params, refs, OPT_KEYS, weights)

print("\n=== PARAM UPDATE ===")
new_params = update_params(params, grads)

print("\n=== NEW EVALUATION ===")
res1 = evaluate_params(session, new_params)
J1 = objective_function(res1, refs, weights)
print("J1 =", J1)
print("VpiL_Vcm =", res1["VpiL_Vcm"])
print("loss_dB_per_cm =", res1["loss_dB_per_cm"])

session.close()