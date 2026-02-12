from modulator_analysis.modulator_lumapi import run_lumerical
from modulator_analysis.file_parsing_scripts.lumerical_electrostatics_mattocsv import convert_lumerical_electrostatics_to_csv
from modulator_analysis.file_parsing_scripts.lumerical_mode_mattocsv import convert_lumerical_mode_to_csv
from modulator_analysis.modulator_overlap import compute_modulator_overlap

# Main
if __name__ == "__main__":
    # Example usage: run with g = 700 nm and Vdc = 100 V
    g_nm = 700
    Vdc = 100.0
    run_lumerical(g_nm, Vdc)
    convert_lumerical_electrostatics_to_csv(Vdc)
    convert_lumerical_mode_to_csv()
    results = compute_modulator_overlap(g_nm)
    print("\n=== Modulator Overlap Results ===")
    print(f"Δn_eff per V: {results['dneff_per_V']:.3e}")
    print(f"χ²_eff_avg (mV): {results['chi2_eff_avg_mV']:.3e}")
    print(f"χ²_eff_avg (pmV): {results['chi2_eff_avg_pmV']:.3e}")
    print(f"Vπ·L (V·m): {results['VpiL_Vm']:.3e}")
    print(f"Vπ·L (V·cm): {results['VpiL_Vcm']:.3e}")