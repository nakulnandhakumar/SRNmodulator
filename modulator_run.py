from modulator_analysis.modulator_lumapi import LumericalSession
from modulator_analysis.modulator_evaluate import evaluate_params
import matplotlib.pyplot as plt
from config import PARAMS

# Define loop over gap values
g = 500e-9

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
VpiL_1V = results["VpiL_1V_Vcm"]

# true VpiL when biased at Vbias
VpiL_true = VpiL_1V / Vbias

print(f"VpiL (1V)               : {VpiL_1V:.3f} V·cm")
print(f"Vbreak                  : {Vbreak:.1f} V ({breakdown_material})")
print(f"Vbias                   : {Vbias:.1f} V")
print(f"VpiL (bias)             : {VpiL_true:.3f} V·cm")
print(f"Loss                    : {results['loss_dB_per_cm']:.3f} dB/cm")
print(f"chi2_eff (1V)           : {results['chi2_eff_avg_pmV']:.3f} pm/V")
print(f"r_eff (1V)              : {results['r_eff_avg_pmV']:.3f} pm/V")
print(f"chi2_eff (bias)         : {results['chi2_eff_avg_pmV'] * Vbias:.3f} pm/V")
print(f"r_eff (bias)            : {results['r_eff_avg_pmV'] * Vbias:.3f} pm/V")
print(f"dneff_per_V             : {results['dneff_per_V']:.3e}")
print(f"dneff (bias)            : {results['dneff_per_V'] * Vbias:.3e}")
print(f"static_dneff_per_Vsq    : {results['static_dneff_per_Vsq']:.3e} per V^2")
print(f"static_dneff (bias)     : {results['static_dneff_per_Vsq'] * (Vbias**2):.4f}")