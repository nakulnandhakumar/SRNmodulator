import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]

# ===================== INIT =====================

supermode = lumapi.MODE(
    hide=False,
    project=r"./lumerical/mode/supermode.lms"
)

with open(r"./lumerical/mode/coupler_switch_supermode.lsf") as f:
    coupler_switch_supermode_script = f.read()

# ===================== CORE FUNCTION =====================

def run_single(pcm_material, g, t_gap_pcm, t_pcm, lum_project=supermode, lsf_script=coupler_switch_supermode_script):

    # Set wavelength in Lumerical
    lam = 1.55e-6
    supermode.putv("lambda", lam)
    
    # Set geometry/material parameters in Lumerical
    supermode.putv("g", g)
    supermode.putv("t_gap_pcm", t_gap_pcm)
    supermode.putv("t_pcm", t_pcm)
    lum_project.putv("pcm_mat", pcm_material)
    
    lum_project.eval(lsf_script)

    nmodes = 6
    mode_data = []

    for m in range(1, nmodes+1):
        name = f"mode{m}"

        try:
            lum_project.eval(f'neff_temp = real(getdata("FDE::data::{name}", "neff"));')
            neff = lum_project.getv("neff_temp")

            lum_project.eval(f'TEfrac_temp = getdata("FDE::data::{name}", "TE polarization fraction");')
            TEfrac = lum_project.getv("TEfrac_temp")

            lum_project.eval(f'x_temp = getdata("FDE::data::{name}", "x");')
            x = np.squeeze(lum_project.getv("x_temp"))

            lum_project.eval(f'y_temp = getdata("FDE::data::{name}", "y");')
            y = np.squeeze(lum_project.getv("y_temp"))

            lum_project.eval(f'Ex_temp = getdata("FDE::data::{name}", "Ex");')
            Ex = np.squeeze(lum_project.getv("Ex_temp"))

            lum_project.eval(f'Ey_temp = getdata("FDE::data::{name}", "Ey");')
            Ey = np.squeeze(lum_project.getv("Ey_temp"))

            lum_project.eval(f'Ez_temp = getdata("FDE::data::{name}", "Ez");')
            Ez = np.squeeze(lum_project.getv("Ez_temp"))

        except:
            print(f"WARNING: failed to get data for mode {m}")
            continue

        X, Y = np.meshgrid(x, y, indexing='ij')
        E2 = np.abs(Ex)**2 + np.abs(Ey)**2 + np.abs(Ez)**2

        # geometry constants (for waveguide masks)
        W = 0.450e-6
        H = 0.350e-6
        margin = 20e-9
        y_core_center = 0
        
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
        # SRN masks
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

        # =====================
        # Add PCM mask
        # =====================

        y_pcm_top = y_pcm_bottom + t_pcm

        mask_pcm = (
            (X >= x_left - W/2 - margin) & (X <= x_left + W/2 + margin) &
            (Y >= y_pcm_bottom) &
            (Y <= y_pcm_top)
        )

        # =====================
        # Energy fractions
        # =====================

        E_total = np.sum(E2)

        eta_left  = np.sum(E2 * mask_left)  / E_total
        eta_right = np.sum(E2 * mask_right) / E_total
        eta_pcm   = np.sum(E2 * mask_pcm)   / E_total

        eta_srn_total = eta_left + eta_right

        mode_data.append({
            "mode": m,
            "neff": neff,
            "TEfrac": TEfrac,
            "eta_left": eta_left,
            "eta_right": eta_right,
            "eta_srn_total": eta_srn_total,
            "eta_pcm": eta_pcm
        })
        
        # print(f"\nMode {m}")
        # print(f"neff = {neff:.6f}")
        # print(f"TEfrac = {TEfrac:.3f}")
        # print(f"eta_left  = {eta_left:.3f}")
        # print(f"eta_right = {eta_right:.3f}")
        # print(f"eta_pcm   = {eta_pcm:.3f}")
        # print(f"eta_srn_total = {eta_srn_total:.3f}")

    # =====================
    # MODE SELECTION
    # =====================

    valid = []
    for md in mode_data:
        if md["TEfrac"] > 0.9:
            if md["eta_pcm"] < 0.15:   # <-- critical filter
                valid.append(md)

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
        "A_max": A_max,
        
        "eta_left_1": m1["eta_left"],
        "eta_right_1": m1["eta_right"],
        "eta_pcm_1": m1["eta_pcm"],

        "eta_left_2": m2["eta_left"],
        "eta_right_2": m2["eta_right"],
        "eta_pcm_2": m2["eta_pcm"],

        "eta_pcm_avg": 0.5 * (m1["eta_pcm"] + m2["eta_pcm"]),
        
        "mode1": m1["mode"],
        "mode2": m2["mode"],
    }


# ===================== PARAMETERS =====================
g = 200e-9
t_gap_pcm = 10e-9
t_pcm = 15e-9

# ===================== RUN BOTH STATES =====================

off = run_single(pcm_material="SBS Amorphous", g=g, t_gap_pcm=t_gap_pcm, t_pcm=t_pcm, lum_project=supermode, lsf_script=coupler_switch_supermode_script)
on  = run_single(pcm_material="SBS Crystalline", g=g, t_gap_pcm=t_gap_pcm, t_pcm=t_pcm, lum_project=supermode, lsf_script=coupler_switch_supermode_script)

# ===================== RESULTS =====================

print("\n========== RESULTS ==========")

print("\nOFF (Amorphous)")
for key, value in off.items():
    if isinstance(value, float):
        print(f"{key} = {value:.6f}")
    else:
        print(f"{key} = {value}")

print("\nON (Crystalline)")
for key, value in on.items():
    if isinstance(value, float):
        print(f"{key} = {value:.6f}")
    else:
        print(f"{key} = {value}")

if off and on:
    print("\n========== SWITCHING ==========")
    print(f"ΔD = {on['D'] - off['D']:.4f}")
    print(f"A_max OFF = {off['A_max']:.4f}")
    print(f"A_max ON  = {on['A_max']:.4f}")