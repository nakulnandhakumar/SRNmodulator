import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]
from file_parsing.lumerical_electrostatics_mattocsv import convert_lumerical_electrostatics_to_csv
from file_parsing.lumerical_mode_mattocsv import convert_lumerical_mode_to_csv
from overlap import compute_modulator_overlap

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

# Run the electrostatics and mode scripts to simulate the device and extract the results
with open(r"./code_verification/electrostatics.lsf") as f:
    charge.eval(f.read())
    
with open(r"./code_verification/mode.lsf") as f:
    mode.eval(f.read())
    
convert_lumerical_electrostatics_to_csv(Vdc=1)
loss_dB_per_cm = convert_lumerical_mode_to_csv()
results = compute_modulator_overlap()

print(f"VpiL(1V) = {results['VpiL_Vcm']:.3f} V·cm")
print(f"loss = {results['loss_dB_per_cm']:.3f} dB/cm")