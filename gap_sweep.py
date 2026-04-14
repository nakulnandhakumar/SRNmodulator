from modulator_analysis.modulator_lumapi import LumericalSession
from modulator_analysis.modulator_evaluate import evaluate_params
import matplotlib.pyplot as plt
from config import PARAMS

# Define loop over gap values
gap_values = [400e-9, 450e-9, 500e-9, 550e-9, 600e-9, 650e-9, 700e-9, 750e-9, 800e-9, 850e-9, 900e-9, 950e-9, 1000e-9]
true_VpiL_results = {}
loss_results = {}
Vbreak_results = {}
chi2_eff_results = {}
pockels_eff_results = {}

# Open Lumerical session and setup geometry
session = LumericalSession()
session.open()

for g in gap_values:
    print(f"\n=== Evaluating gap g = {g*1e9:.0f} nm ===")

    # Update gap in parameters
    params = PARAMS.copy()
    params["g"] = g
    params["t_shield_gapR"] = 0.5 * g
    params["t_shield_gapL"] = 0.5 * g
    params["t_shield_core"] = 0.5 * g
    params["t_shield_metal"] = 0.5 * g
    
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
    print(f"static_dneff (bias)     : {results['static_dneff_per_Vsq'] * (Vbias**2):.4f}")
    
    true_VpiL_results[g] = VpiL_true
    loss_results[g] = results["loss_dB_per_cm"]
    chi2_eff_results[g] = results["chi2_eff_avg_pmV"]
    pockels_eff_results[g] = results["r_eff_avg_pmV"]
    Vbreak_results[g] = Vbreak
    
# Plot the result for true VpiL vs gap
plt.figure(figsize=(6, 5))
plt.plot(list(true_VpiL_results.keys()), list(true_VpiL_results.values()), marker='o')
plt.xlabel("Gap (nm)")
plt.ylabel("True VpiL (V·cm)")
plt.title("True VpiL vs Gap")
plt.grid()
plt.show()

# Plot the result for loss vs gap
plt.figure(figsize=(6, 5))
plt.plot(list(loss_results.keys()), list(loss_results.values()), marker='o', color='orange')
plt.xlabel("Gap (nm)")
plt.ylabel("Loss (dB/cm)")
plt.title("Loss vs Gap")
plt.grid()
plt.show()

# Plot the result for breakdown voltage vs gap
plt.figure(figsize=(6, 5))
plt.plot(list(Vbreak_results.keys()), list(Vbreak_results.values()), marker='o', color='green')
plt.xlabel("Gap (nm)")
plt.ylabel("Breakdown Voltage (V)")
plt.title("Breakdown Voltage vs Gap")
plt.grid()
plt.show()