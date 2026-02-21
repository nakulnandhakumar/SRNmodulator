import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]


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

    def setup_geometry(self):
        """
        Run once. Builds geometry.
        """
        with open(r"./lumerical/electrostatics/setup_geometry_electrostatics.lsf") as f:
            self.charge.eval(f.read())

        with open(r"./lumerical/mode/setup_geometry_mode.lsf") as f:
            self.mode.eval(f.read())

    def run_simulation(self, params):
        """
        Called every evaluation.
        Updates parameters and runs.
        """

        # --- DEVICE ---
        self.charge.eval("switchtolayout;")

        for k, v in params.items():
            self.charge.putv(k, v)

        with open(r"./lumerical/electrostatics/run_electrostatics.lsf") as f:
            self.charge.eval(f.read())

        # --- MODE ---
        self.mode.eval("switchtolayout;")

        for k, v in params.items():
            self.mode.putv(k, v)

        with open(r"./lumerical/mode/run_mode.lsf") as f:
            self.mode.eval(f.read())