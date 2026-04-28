import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]

# Initialize Lumerical MODE for the ring filter waveguide
ring_supermode = lumapi.MODE(
            hide=False,
            project=r"./lumerical/mode/ring_supermode.lms"
        )

with open(r"./lumerical/mode/ring_filter_supermode.lsf") as f:
    eta_sweep_script = f.read()

material_params = {
    "core_material_mode": "SRN 3.1 (Silicon Rich Nitride)",
    "clad_left_material": "SiO2 (Glass) - Palik",
    "clad_right_material": "SBS Amorphous",
    "BOX_cladding_material_mode": "SiO2 (Glass) - Palik",
}

for param, value in material_params.items():
    ring_supermode.putv(param, value)

ring_supermode.putv("lambda", 1.55e-6)

# Geometry (constant)
W = 0.450e-6
H = 0.350e-6
g = 0.700e-6
t_buffer = 185e-9
tBOX = 3e-6
tCLAD = 2e-6

lam = 1.55e-6
Lc = 5e-6
margin = 20e-9
k_pcm = 0.00216

alpha_pcm_m = 4*np.pi*k_pcm/lam
alpha_pcm_dB_cm = alpha_pcm_m * (10/np.log(10)) / 100

results = []

pcm_w_values = np.linspace(50e-9, 400e-9, 25)
for pcm_w in pcm_w_values:

    y_core_center = tBOX + H/2

    # Left / right cladding centers
    x_left  = -(W/2 + g/2)
    x_right =  (W/2 + g/2)
    
    ring_supermode.putv("pcm_w", pcm_w)
    ring_supermode.eval(eta_sweep_script)

    nmodes = 6  # should match Lumerical trial modes

    mode_data = []

    for m in range(1, nmodes+1):
        mode_name = f"mode{m}"

        try:
            # --- basic properties ---
            ring_supermode.eval(f'neff_temp = real(getdata("{mode_name}", "neff"));')
            neff = ring_supermode.getv("neff_temp")

            ring_supermode.eval(f'TEfrac_temp = getdata("{mode_name}", "TE polarization fraction");')
            TEfrac = ring_supermode.getv("TEfrac_temp")

            ring_supermode.eval(f'loss_temp = getdata("{mode_name}", "loss");')
            supermode_loss = ring_supermode.getv("loss_temp") # dB/m
            supermode_loss_dB_cm = supermode_loss / 100

            ring_supermode.eval(f'x_temp = getdata("FDE::data::{mode_name}","x");')
            x = np.squeeze(ring_supermode.getv("x_temp"))
            
            ring_supermode.eval(f'y_temp = getdata("FDE::data::{mode_name}","y");')
            y = np.squeeze(ring_supermode.getv("y_temp"))

            ring_supermode.eval(f'Ex_temp = getdata("{mode_name}", "Ex");')
            Ex = np.squeeze(ring_supermode.getv("Ex_temp"))

            ring_supermode.eval(f'Ey_temp = getdata("{mode_name}", "Ey");')
            Ey = np.squeeze(ring_supermode.getv("Ey_temp"))

            ring_supermode.eval(f'Ez_temp = getdata("{mode_name}", "Ez");')
            Ez = np.squeeze(ring_supermode.getv("Ez_temp"))

        except:
            print(f"WARNING: Mode {mode_name} not found")
            input("Press Enter to continue...")
            continue  # skip missing modes safely

        # --- grids ---
        X, Y = np.meshgrid(x, y, indexing='ij')
        
        # --- intensity ---
        E2 = np.abs(Ex)**2 + np.abs(Ey)**2 + np.abs(Ez)**2
        
        # Masks
        margin = 20e-9

        # --- SRN core positions ---
        x_bus_center  = -(W/2 + g/2)
        x_ring_center =  (W/2 + g/2)

        mask_srn_bus = (
            (X >= x_bus_center - W/2 - margin) & (X <= x_bus_center + W/2 + margin) &
            (Y >= y_core_center - H/2 - margin) & (Y <= y_core_center + H/2 + margin)
        )
 
        mask_srn_ring = (
            (X >= x_ring_center - W/2 - margin) & (X <= x_ring_center + W/2 + margin) &
            (Y >= y_core_center - H/2 - margin) & (Y <= y_core_center + H/2 + margin)
        )

        # total SRN (both waveguides)
        mask_srn_total = mask_srn_bus | mask_srn_ring

        # Split plane (midpoint between waveguides)
        x_split = 0

        # PCM is in the middle of the gap, separated from each SRN core by t_buffer
        pcm_half_width = pcm_w / 2

        if pcm_half_width <= 0:
            print("WARNING: buffer too large; no PCM region left")
            continue

        mask_pcm_total = (
            (np.abs(X) <= pcm_half_width) &
            (Y >= y_core_center - H/2 - margin) &
            (Y <= y_core_center + H/2 + margin)
        )

        mask_pcm_ring = mask_pcm_total & (X > 0)
        mask_pcm_bus  = mask_pcm_total & (X < 0)

        E_total = np.sum(E2)

        E_srn_total = np.sum(E2 * mask_srn_total)
        E_pcm_ring  = np.sum(E2 * mask_pcm_ring)
        E_pcm_total = np.sum(E2 * mask_pcm_total)

        eta_srn_total = E_srn_total / E_total
        eta_pcm_ring  = E_pcm_ring  / E_total
        eta_pcm_total = E_pcm_total / E_total

        mode_data.append({
            "mode": m,
            "neff": neff,
            "eta_srn_total": eta_srn_total,
            "eta_pcm_total": eta_pcm_total,
            "eta_pcm_ring": eta_pcm_ring,
            "supermode_loss_dB_cm": supermode_loss_dB_cm,
            "TEfrac": TEfrac
        })
        
    # Select valid TE modes where SRN dominates PCM
    TE_threshold = 0.90

    valid_modes = [
        md for md in mode_data
        if (md["TEfrac"] > TE_threshold)
        and (md["eta_srn_total"] > md["eta_pcm_total"])
    ]

    if len(valid_modes) < 2:
        print("WARNING: Fewer than two valid SRN-like TE modes found")
        continue

    # For coupling, pick the two SRN-like TE modes with highest neff
    # These should be the even/odd SRN supermodes.
    srn_modes = sorted(valid_modes, key=lambda x: x["neff"], reverse=True)

    mode_high = srn_modes[0]
    mode_low  = srn_modes[1]

    lam = 1.55e-6

    # ============================================================
    # Coupling + loss physics (CLEAN)
    # ============================================================

    # Supermode splitting → coupling
    dneff = abs(mode_high["neff"] - mode_low["neff"])
    kappa_prime = (np.pi/lam) * dneff   # = dBeta/2

    # Coupling phase
    kappa_L = kappa_prime * Lc

    # Ideal powers
    P_cross_ideal = np.sin(kappa_L)**2
    P_through_ideal = np.cos(kappa_L)**2

    # 100% coupling length (important design metric)
    L_100 = np.pi / (2 * kappa_prime)

    # PCM absorption → ring-side loss
    eta_pcm_ring_avg = 0.5 * (
        mode_high["eta_pcm_ring"] + mode_low["eta_pcm_ring"]
    )

    loss_ring_dB_cm = eta_pcm_ring_avg * alpha_pcm_dB_cm

    # Convert to coupler loss
    loss_coupler_dB = loss_ring_dB_cm * (Lc * 100)

    # Include loss penalty
    loss_linear = 10 ** (-loss_coupler_dB / 10)

    P_cross_lossy = P_cross_ideal * loss_linear
    P_through_lossy = P_through_ideal * loss_linear

    # How close you are to π/2 coupling
    coupling_error = abs(kappa_L - np.pi/2)

    # Store everything useful later
    result = {
        "pcm_w_nm": pcm_w * 1e9,

        # modes
        "mode_high": mode_high["mode"],
        "mode_low": mode_low["mode"],

        # effective indices
        "neff_high": mode_high["neff"],
        "neff_low": mode_low["neff"],
        "neff_avg": 0.5 * (mode_high["neff"] + mode_low["neff"]),
        "delta_neff": dneff,

        # coupling physics
        "kappa_prime": kappa_prime,
        "kappa_L": kappa_L,
        "L_100_um": L_100 * 1e6,
        "coupling_error": coupling_error,

        # power transfer
        "P_cross_ideal": P_cross_ideal,
        "P_cross_lossy": P_cross_lossy,
        "P_through_ideal": P_through_ideal,
        "P_through_lossy": P_through_lossy,

        # loss
        "loss_ring_dB_cm": loss_ring_dB_cm,
        "loss_coupler_dB": loss_coupler_dB,

        # mode purity
        "eta_pcm_total": 0.5 * (
            mode_high["eta_pcm_total"] + mode_low["eta_pcm_total"]
        ),
        "eta_pcm_ring": eta_pcm_ring_avg,
    }

    results.append(result)

    print("====================================")
    print(f"PCM width = {pcm_w*1e9:.1f} nm")
    print(f"kappa_L = {kappa_L:.4f} (target ~1.57)")
    print(f"P_cross (ideal) = {P_cross_ideal:.3f}")
    print(f"P_cross (lossy) = {P_cross_lossy:.3f}")
    print(f"L_100 = {L_100*1e6:.2f} um")
    print(f"loss_coupler = {loss_coupler_dB:.3f} dB")
    print("====================================")