from modulator_analysis.modulator_lumapi import run_lumerical
from modulator_analysis.file_parsing_scripts.lumerical_electrostatics_mattocsv import convert_lumerical_electrostatics_to_csv
from modulator_analysis.file_parsing_scripts.lumerical_mode_mattocsv import convert_lumerical_mode_to_csv
from modulator_analysis.modulator_overlap import compute_modulator_overlap

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
t_shield_gapR = 350e-9     # thickness of the shield within the right gap in meters
t_shield_gapL = 350e-9    # thickness of the shield within the left gap in meters
t_shield_core = 350e-9    # thickness of the shield above the core in meters
t_shield_metal = 350e-9   # thickness of the shield above the metal electrodes in meters

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

# Main
if __name__ == "__main__":
    # Example usage: run with g = 700 nm and Vdc = 100 V
    run_lumerical(params)
    convert_lumerical_electrostatics_to_csv(Vdc)
    convert_lumerical_mode_to_csv()
    results = compute_modulator_overlap(params)
    print("\n=== Modulator Overlap Results ===")
    print(f"Δn_eff per V: {results['dneff_per_V']:.3e}")
    print(f"χ²_eff_avg (mV): {results['chi2_eff_avg_mV']:.3e}")
    print(f"χ²_eff_avg (pmV): {results['chi2_eff_avg_pmV']:.3e}")
    print(f"Vπ·L (V·m): {results['VpiL_Vm']:.3e}")
    print(f"Vπ·L (V·cm): {results['VpiL_Vcm']:.3e}")