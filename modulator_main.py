from modulator_analysis.modulator_lumapi import run_lumerical

# Main
if __name__ == "__main__":
    # Example usage: run with g = 700 nm and Vdc = 100 V
    g_nm = 700
    Vdc = 100.0
    run_lumerical(g_nm, Vdc)