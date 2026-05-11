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

def run_single(pcm_material_coupler, pcm_material_bus, g, t_gap_pcm, t_pcm, coupling="lateral",lum_project=supermode, lsf_script=coupler_switch_supermode_script):

    # Set wavelength in Lumerical
    lam = 1.55e-6
    lum_project.putv("lambda", lam)
    
    # Check if coupling is vertical or lateral
    if coupling == "vertical":
        lum_project.putv("W", 350e-9)
        lum_project.putv("H", 450e-9)
    elif coupling == "lateral":
        lum_project.putv("W", 450e-9)
        lum_project.putv("H", 350e-9)
    else:
        print(f"ERROR: invalid coupling type '{coupling}'")
        return None
    
    # Set geometry/material parameters in Lumerical
    lum_project.putv("g", g)
    lum_project.putv("t_gap_pcm", t_gap_pcm)
    lum_project.putv("t_pcm", t_pcm)
    lum_project.putv("pcm_mat_left", pcm_material_coupler)   # PCM on left waveguide
    lum_project.putv("pcm_mat_right", pcm_material_bus) # PCM on right waveguide

    lum_project.eval(lsf_script)

    nmodes = 4
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
            
            lum_project.eval(f'loss_temp = real(getdata("FDE::data::{name}", "loss"));')
            loss_dB_m = lum_project.getv("loss_temp")    # dB/m
            loss_dB_cm = loss_dB_m / 100  # dB/cm

        except:
            print(f"WARNING: failed to get data for mode {m}")
            continue

        X, Y = np.meshgrid(x, y, indexing='ij')
        E2 = np.abs(Ex)**2 + np.abs(Ey)**2 + np.abs(Ez)**2

        # geometry constants (for waveguide masks)
        if coupling == "vertical":
            W = 350e-9
            H = 450e-9
        else:
            W = 450e-9
            H = 350e-9
        
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

        srn_mask_left = (
            (X >= x_left - W/2 - margin) & (X <= x_left + W/2 + margin) &
            (Y >= y_bot_core - margin) &
            (Y <= y_mask_top)
        )

        srn_mask_right = (
            (X >= x_right - W/2 - margin) & (X <= x_right + W/2 + margin) &
            (Y >= y_bot_core - margin) &
            (Y <= y_mask_top)
        )

        # =====================
        # Add PCM mask
        # =====================

        y_pcm_top = y_pcm_bottom + t_pcm

        mask_pcm_left = (
            (X >= x_left - W/2 - margin) & (X <= x_left + W/2 + margin) &
            (Y >= y_pcm_bottom) &
            (Y <= y_pcm_top)
        )

        mask_pcm_right = (
            (X >= x_right - W/2 - margin) & (X <= x_right + W/2 + margin) &
            (Y >= y_pcm_bottom) &
            (Y <= y_pcm_top)
        )

        # =====================
        # Energy fractions
        # =====================

        E_total = np.sum(E2)

        eta_left  = np.sum(E2 * srn_mask_left)  / E_total
        eta_right = np.sum(E2 * srn_mask_right) / E_total
        
        eta_pcm_left  = np.sum(E2 * mask_pcm_left) / E_total
        eta_pcm_right = np.sum(E2 * mask_pcm_right) / E_total
        
        eta_srn_total = eta_left + eta_right
        eta_pcm_total = eta_pcm_left + eta_pcm_right

        mode_data.append({
            "mode": m,
            "neff": neff,
            "TEfrac": TEfrac,
            "loss_dB_cm": loss_dB_cm,
            "eta_left": eta_left,
            "eta_right": eta_right,
            "eta_srn_total": eta_srn_total,
            "eta_pcm_left": eta_pcm_left,
            "eta_pcm_right": eta_pcm_right,
            "eta_pcm_total": eta_pcm_total
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
            if md["eta_pcm_left"] < 0.15 and md["eta_pcm_right"] < 0.15:   # <-- critical filter
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
    D = abs(m1["eta_right"] - m2["eta_right"])

    A_max = 1 - D**2
    
    # Effective loss (weighted by excitation)
    loss1 = m1["loss_dB_cm"]
    loss2 = m2["loss_dB_cm"]

    # excitation weights (input waveguide)
    w1 = m1["eta_right"]
    w2 = m2["eta_right"]

    norm = w1 + w2 + 1e-15
    w1 /= norm
    w2 /= norm

    loss_eff = w1 * loss1 + w2 * loss2   # dB/cm

    return {
        "neff1": m1["neff"],
        "neff2": m2["neff"],
        "dneff": dneff,
        "Omega": Omega,
        "D": D,
        "A_max": A_max,
        
        "eta_left_1": m1["eta_left"],
        "eta_right_1": m1["eta_right"],
        "eta_pcm_left_1": m1["eta_pcm_left"],
        "eta_pcm_right_1": m1["eta_pcm_right"],

        "eta_left_2": m2["eta_left"],
        "eta_right_2": m2["eta_right"],
        "eta_pcm_left_2": m2["eta_pcm_left"],
        "eta_pcm_right_2": m2["eta_pcm_right"],

        "eta_pcm_avg": 0.5 * (m1["eta_pcm_total"] + m2["eta_pcm_total"]),
        
        "loss1": loss1,
        "loss2": loss2,
        "loss_eff": loss_eff,
        
        "mode1": m1["mode"],
        "mode2": m2["mode"],
    }


# ===================== PARAMETERS =====================
g = 250e-9
t_gap_pcm = 0e-9
t_pcm = 50e-9

# ===================== RUN BOTH STATES =====================

antisym = run_single(pcm_material_coupler="SBS Amorphous", pcm_material_bus="SBS Crystalline", g=g, t_gap_pcm=t_gap_pcm, t_pcm=t_pcm, lum_project=supermode, coupling="lateral", lsf_script=coupler_switch_supermode_script)
sym  = run_single(pcm_material_coupler="SBS Crystalline", pcm_material_bus="SBS Crystalline", g=g, t_gap_pcm=t_gap_pcm, t_pcm=t_pcm, lum_project=supermode, coupling="lateral", lsf_script=coupler_switch_supermode_script)

# ===================== RESULTS =====================

print("\n========== RESULTS ==========")

print("\nASYMMETRIC (NO COUPLING)")
for key, value in antisym.items():
    if isinstance(value, float):
        print(f"{key} = {value:.6f}")
    else:
        print(f"{key} = {value}")

print("\nSYMMETRIC (STRONG COUPLING)")
for key, value in sym.items():
    if isinstance(value, float):
        print(f"{key} = {value:.6f}")
    else:
        print(f"{key} = {value}")

if antisym and sym:

    # =====================
    # DESIGN LENGTH (from symmetric state)
    # =====================
    L = np.pi / (2 * sym["Omega"])   # meters

    # =====================
    # ACTUAL POWER TRANSFER
    # =====================
    P_antisym = (1 - antisym["D"]**2) * np.sin(antisym["Omega"] * L)**2
    P_sym  = (1 - sym["D"]**2)  * np.sin(sym["Omega"]  * L)**2

    # avoid log(0)
    P_sym_safe = max(P_sym, 1e-12)

    ER_dB = 10 * np.log10(P_sym_safe / P_antisym)

    # =====================
    # PRINT RESULTS
    # =====================
    print("\n========== SWITCHING ==========")
    print(f"L_design (um) = {L*1e6:.3f}")
    print(f"P_antisym = {P_antisym:.4f}")
    print(f"P_sym  = {P_sym:.4f}")
    print(f"ER (dB) = {ER_dB:.2f}")