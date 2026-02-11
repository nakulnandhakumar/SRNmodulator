import sys
import os
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]

def run_lumerical(g_nm, Vdc):
    g = g_nm * 1e-9

    # ---------- CHARGE ----------
    project_path_electrostatics = r"./lumerical_projects/electrostatics/modulator_electrostatics.ldev"
    charge = lumapi.DEVICE(hide=False, project=project_path_electrostatics)
    
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
    project_path_mode = r"./lumerical_projects/mode/modulator_mode.ldev"
    mode = lumapi.MODE(hide=False, project=project_path_mode)

    try:
        mode.putv("g", g)
        lsf_path_mode = r"./lumerical_scripts/SRN_modulator_mode.lsf"
        with open(lsf_path_mode, "r") as f:
            code = f.read()
        mode.eval(code)
        
    except Exception as e:
        print("\n=== LUMERICAL ERROR ===")
        print(e)
        print("Leaving Lumerical open for inspection.")
        input("Press ENTER after you inspect the Lumerical Script Prompt...")
    
    mode.close()