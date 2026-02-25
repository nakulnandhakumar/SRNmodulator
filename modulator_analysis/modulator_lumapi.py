import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]
import numpy as np

def clamp_params(p):
    p = p.copy()
    eps = 10e-9  # 10 nm minimum

    # gap
    p["g"] = float(np.clip(p["g"], 150e-9, 3e-6))
    g = p["g"]

    # shield thicknesses
    for k in ["t_shield_gapR","t_shield_gapL","t_shield_core","t_shield_metal"]:
        if k in p:
            p[k] = float(np.clip(p[k], eps, 0.9*g))

    # metal thickness
    if "metal_t" in p:
        p["metal_t"] = float(np.clip(p["metal_t"], 20e-9, 500e-9))

    return p

class LumericalSession:

    def __init__(self):
        self.charge = None
        self.mode = None

    def open(self):
        self.charge = lumapi.DEVICE(
            hide=False,
            project=r"./lumerical/electrostatics/modulator_electrostatics.ldev"
        )

        self.mode = lumapi.MODE(
            hide=False,
            project=r"./lumerical/mode/modulator_mode.ldev"
        )

    def close(self):
        if self.charge:
            self.charge.close()
        if self.mode:
            self.mode.close()

    def setup_geometry(self, params):
        """
        Run once. Builds geometry.
        """
        for k, v in params.items():
            self.charge.putv(k, v)
        with open(r"./lumerical/electrostatics/setup_geometry_electrostatics.lsf") as f:
            self.charge.eval(f.read())

        for k, v in params.items():
            self.mode.putv(k, v)
        with open(r"./lumerical/mode/setup_geometry_mode.lsf") as f:
            self.mode.eval(f.read())

    def run_simulation(self, params):
        """
        Called every evaluation.
        Updates parameters and runs.
        """
        
        params = clamp_params(params)
        
        # --- DEVICE ---
        self.charge.eval("switchtolayout;")

        for k, v in params.items():
            self.charge.putv(k, v)

        with open(r"./lumerical/electrostatics/update_and_run_electrostatics.lsf") as f:
            self.charge.eval(f.read())

        # --- MODE ---
        self.mode.eval("switchtolayout;")

        for k, v in params.items():
            self.mode.putv(k, v)

        with open(r"./lumerical/mode/update_and_run_mode.lsf") as f:
            self.mode.eval(f.read())