import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]

# ============================================================
# Lumerical session management
# ============================================================

charge = lumapi.DEVICE(
    hide=False, 
    project=r"./lumerical/electrostatics/modulator_electrostatics.ldev"
)

mode = lumapi.MODE(
    hide=False,
    project=r"./lumerical/mode/modulator_mode.ldev"
)