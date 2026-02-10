import sys
import os
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi

def run_lumerical(g_nm, Vdc):
    g = g_nm * 1e-9

    # ---------- CHARGE ----------
    charge = lumapi.DEVICE(hide=False)
    
    try:
        charge.putv("g", g)
        charge.putv("Vdc", Vdc)
        lsf_path_electrostatics = r"./lumerical_scripts/SRN_modulator_electrostatics.lsf"

        with open(lsf_path_electrostatics, "r") as f:
            code = f.read()

        charge.eval(code)

    except Exception as e:
        print("\n=== LUMERICAL ERROR ===")
        print(e)
        print("Leaving Lumerical open for inspection.")
        input("Press ENTER after you inspect the Lumerical Script Prompt...")

    # only close if successful
    charge.close()

    # ---------- MODE ----------
    mode = lumapi.MODE(hide=False)
    mode.putv("g", g)
    lsf_path_mode = r"./lumerical_scripts/SRN_modulator_mode.lsf"
    lum_mode_code = open(lsf_path_mode, "r").read()
    mode.eval(lum_mode_code)
    mode.close()
    
if __name__ == "__main__":
    # Example usage: run with g = 700 nm and Vdc = 100 V
    g_nm = 700
    Vdc = 100.0
    run_lumerical(g_nm, Vdc)