import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]

# ===================== INIT =====================

mode = lumapi.MODE(
    hide=False,
    project=r"./lumerical/mode/supermode.lms"
)

with open(r"./lumerical/mode/coupler_switch_supermode.lsf") as f:
    lsf_script = f.read()

# ===================== PARAMETERS =====================

lam = 1.55e-6
mode.putv("lambda", lam)

# >>> SET DESIGN PARAMETERS HERE <<<
g = 200e-9
t_gap_pcm = 10e-9
t_pcm = 15e-9

mode.putv("g", g)
mode.putv("t_gap_pcm", t_gap_pcm)
mode.putv("t_pcm", t_pcm)

# geometry constants (for masks)
W = 0.450e-6
H = 0.350e-6
margin = 20e-9
y_core_center = 0

# ===================== CORE FUNCTION =====================

def run_single(pcm_material):

    mode.putv("pcm_mat", pcm_material)
    mode.eval(lsf_script)

    nmodes = 6
    mode_data = []

    for m in range(1, nmodes+1):
        name = f"mode{m}"

        try:
            mode.eval(f'neff_temp = real(getdata("FDE::data::{name}", "neff"));')
            neff = mode.getv("neff_temp")

            mode.eval(f'TEfrac_temp = getdata("FDE::data::{name}", "TE polarization fraction");')
            TEfrac = mode.getv("TEfrac_temp")

            mode.eval(f'x_temp = getdata("FDE::data::{name}", "x");')
            x = np.squeeze(mode.getv("x_temp"))

            mode.eval(f'y_temp = getdata("FDE::data::{name}", "y");')
            y = np.squeeze(mode.getv("y_temp"))

            mode.eval(f'Ex_temp = getdata("FDE::data::{name}", "Ex");')
            Ex = np.squeeze(mode.getv("Ex_temp"))

            mode.eval(f'Ey_temp = getdata("FDE::data::{name}", "Ey");')
            Ey = np.squeeze(mode.getv("Ey_temp"))

            mode.eval(f'Ez_temp = getdata("FDE::data::{name}", "Ez");')
            Ez = np.squeeze(mode.getv("Ez_temp"))

        except:
            print(f"WARNING: failed to get data for mode {m}")
            continue

        X, Y = np.meshgrid(x, y, indexing='ij')
        E2 = np.abs(Ex)**2 + np.abs(Ey)**2 + np.abs(Ez)**2

        # =====================
        # LEFT = PCM-loaded WG
        # RIGHT = clean WG
        # =====================

        x_left  = -(W/2 + g/2)
        x_right =  (W/2 + g/2)
        
        # =====================
        # Vertical boundaries
        # =====================

        y_top_core = y_core_center + H/2
        y_bot_core = y_core_center - H/2

        # PCM starts above the core
        y_pcm_bottom = y_top_core + t_gap_pcm

        # safety buffer (avoid counting PCM field)
        buffer = 2e-9

        # =====================
        # Compute mask top safely
        # =====================

        # Ideal: include margin but stop before PCM
        y_mask_top_candidate = y_top_core + margin
        y_pcm_limit = y_pcm_bottom - buffer

        # Handle edge cases
        if t_gap_pcm <= buffer:
            # PCM touching or too close → NO upward margin
            y_mask_top = y_top_core
        else:
            y_mask_top = min(y_mask_top_candidate, y_pcm_limit)

        # =====================
        # Final masks
        # =====================

        mask_left = (
            (X >= x_left - W/2 - margin) & (X <= x_left + W/2 + margin) &
            (Y >= y_bot_core - margin) &
            (Y <= y_mask_top)
        )

        mask_right = (
            (X >= x_right - W/2 - margin) & (X <= x_right + W/2 + margin) &
            (Y >= y_bot_core - margin) &
            (Y <= y_mask_top)
        )

        E_total = np.sum(E2)
        eta_left = np.sum(E2 * mask_left) / E_total
        eta_right = np.sum(E2 * mask_right) / E_total

        mode_data.append({
            "mode": m,
            "neff": neff,
            "TEfrac": TEfrac,
            "eta_left": eta_left,
            "eta_right": eta_right
        })

    # =====================
    # MODE SELECTION
    # =====================

    valid = [md for md in mode_data if md["TEfrac"] > 0.9]

    if len(valid) < 2:
        print("ERROR: not enough valid modes")
        return None

    modes = sorted(valid, key=lambda x: x["neff"], reverse=True)

    m1 = modes[0]
    m2 = modes[1]

    # =====================
    # PHYSICS
    # =====================

    dneff = abs(m1["neff"] - m2["neff"])
    Omega = (np.pi / lam) * dneff

    # Detuning proxy
    D = abs(m1["eta_left"] - m2["eta_left"])

    A_max = 1 - D**2

    return {
        "neff1": m1["neff"],
        "neff2": m2["neff"],
        "dneff": dneff,
        "Omega": Omega,
        "D": D,
        "A_max": A_max
    }

# ===================== RUN BOTH STATES =====================

off = run_single("SBS Amorphous")
on  = run_single("SBS Crystalline")

# ===================== RESULTS =====================

print("\n========== RESULTS ==========")

print("\nOFF (Amorphous)")
print(off)

print("\nON (Crystalline)")
print(on)

if off and on:
    print("\n========== SWITCHING ==========")
    print(f"ΔD = {on['D'] - off['D']:.4f}")
    print(f"A_max OFF = {off['A_max']:.4f}")
    print(f"A_max ON  = {on['A_max']:.4f}")