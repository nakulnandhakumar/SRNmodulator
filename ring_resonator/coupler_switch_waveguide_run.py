import numpy as np
import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi  # pyright: ignore

# ============================================================
# Initialize MODE
# ============================================================

supermode = lumapi.MODE(
    hide=False,
    project=r"./lumerical/mode/supermode.lms"
)

with open(r"./lumerical/mode/coupler_switch_waveguide_run.lsf") as f:
    script = f.read()

# ============================================================
# PARAMETERS
# ============================================================

t_buffer = 190e-9

material_params = {
    "core_material_mode": "SRN 3.1 (Silicon Rich Nitride)",
    "clad_left_material": "SiO2 (Glass) - Palik",
    "clad_right_material": "SBS Crystalline",
    "BOX_cladding_material_mode": "SiO2 (Glass) - Palik",
}

for param, value in material_params.items():
    supermode.putv(param, value)

supermode.putv("t_buffer", t_buffer)
supermode.eval(script)

# ============================================================
# GEOMETRY (must match LSF)
# ============================================================

W = 0.450e-6
H = 0.350e-6
g = 0.700e-6

tBOX = 3e-6
y_core_center = tBOX + H/2

margin = 20e-9

# ============================================================
# MODE EXTRACTION
# ============================================================

nmodes = 4
mode_data = []

for m in range(1, nmodes+1):
    mode_name = f"mode{m}"

    try:
        # --- scalar properties ---
        supermode.eval(f'neff_temp = real(getdata("FDE::data::{mode_name}", "neff"));')
        neff = supermode.getv("neff_temp")

        supermode.eval(f'TEfrac_temp = getdata("FDE::data::{mode_name}", "TE polarization fraction");')
        TEfrac = supermode.getv("TEfrac_temp")

        supermode.eval(f'loss_temp = getdata("FDE::data::{mode_name}", "loss");')
        loss = supermode.getv("loss_temp")
        loss_dB_cm = loss / 100

        # --- grid ---
        supermode.eval(f'x_temp = getdata("FDE::data::{mode_name}", "x");')
        x = np.squeeze(supermode.getv("x_temp"))

        supermode.eval(f'y_temp = getdata("FDE::data::{mode_name}", "y");')
        y = np.squeeze(supermode.getv("y_temp"))

        # --- fields ---
        supermode.eval(f'Ex_temp = getdata("FDE::data::{mode_name}", "Ex");')
        Ex = np.squeeze(supermode.getv("Ex_temp"))

        supermode.eval(f'Ey_temp = getdata("FDE::data::{mode_name}", "Ey");')
        Ey = np.squeeze(supermode.getv("Ey_temp"))

        supermode.eval(f'Ez_temp = getdata("FDE::data::{mode_name}", "Ez");')
        Ez = np.squeeze(supermode.getv("Ez_temp"))

    except:
        print(f"WARNING: Mode {mode_name} not found")
        continue

    # ============================================================
    # FIELD PROCESSING
    # ============================================================

    E2 = np.abs(Ex)**2 + np.abs(Ey)**2 + np.abs(Ez)**2
    E_total = np.sum(E2)

    if E_total == 0:
        continue

    X, Y = np.meshgrid(x, y, indexing='ij')

    mask_srn = (
        (X >= -W/2 - margin) & (X <= W/2 + margin) &
        (Y >= y_core_center - H/2 - margin) & (Y <= y_core_center + H/2 + margin)
    )

    mask_pcm = (
        (X >= W/2 + t_buffer) & (X <= W/2 + g) &
        (Y >= y_core_center - H/2 - margin) & (Y <= y_core_center + H/2 + margin)
    )

    E_srn = np.sum(E2 * mask_srn)
    E_pcm = np.sum(E2 * mask_pcm)

    eta_srn = E_srn / E_total
    eta_pcm = E_pcm / E_total

    mode_data.append({
        "mode": m,
        "neff": neff,
        "eta_srn": eta_srn,
        "eta_pcm": eta_pcm,
        "loss_dB_cm": loss_dB_cm,
        "TEfrac": TEfrac
    })

# ============================================================
# MODE SELECTION
# ============================================================

TE_threshold = 0.90

valid_modes = [
    md for md in mode_data
    if (md["TEfrac"] > TE_threshold) and (md["eta_srn"] > md["eta_pcm"])
]

if len(valid_modes) == 0:
    print("No valid SRN-dominated TE modes found")
    exit()

# sort by SRN dominance
valid_modes = sorted(valid_modes, key=lambda x: x["eta_srn"], reverse=True)

best_mode = valid_modes[0]

# ============================================================
# OUTPUT
# ============================================================

print("====================================")
print(f"Buffer thickness = {t_buffer*1e9:.1f} nm")
print(f"Selected mode = {best_mode['mode']}")
print(f"neff = {best_mode['neff']:.4f}")
print(f"TE fraction = {best_mode['TEfrac']:.4f}")
print(f"eta_pcm = {best_mode['eta_pcm']:.4f}")
print(f"eta_good = {1-best_mode['eta_pcm']:.4f}")
print(f"loss = {best_mode['loss_dB_cm']:.4f} dB/cm")
print("====================================")