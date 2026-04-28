import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]

# ============================================================
# Sweep buffer thickness and observe mode profiles
# ============================================================

# Initialize Lumerical MODE for the ring filter waveguide
ring_supermode = lumapi.MODE(
            hide=False,
            project=r"./lumerical/mode/ring_supermode.lms"
        )

with open(r"./lumerical/mode/ring_filter_waveguide_run.lsf") as f:
    eta_sweep_script = f.read()
    
t_buffer_values = np.linspace(100e-9, 200e-9, 20)  # Sweep buffer thickness from 0 to 100 nm

material_params = {
    "core_material_mode": "SRN 3.1 (Silicon Rich Nitride)",
    "clad_left_material": "SiO2 (Glass) - Palik",
    "clad_right_material": "SBS Amorphous",
    "BOX_cladding_material_mode": "SiO2 (Glass) - Palik",
}

for param, value in material_params.items():
    ring_supermode.putv(param, value)

pcm_confinement_results = []
good_confinement_results = []
loss_results = []

for t_buffer in t_buffer_values:
    
    # Define geometric parameters
    W = 0.450e-6
    H = 0.350e-6
    g = 0.700e-6

    tBOX = 3e-6
    tCLAD = 2e-6

    Xext = 4e-6
    Ytop_margin = 2e-6
    Ybot_margin = 2e-6

    y_core_center = tBOX + H/2

    y_span_SiO2 = tBOX + H + tCLAD + Ytop_margin + Ybot_margin
    y_SiO2_center = -Ybot_margin + y_span_SiO2/2

    # Left / right cladding centers
    x_left  = -(W/2 + g/2)
    x_right =  (W/2 + g/2)

    # remaining gap after buffer
    remaining_gap = g - t_buffer
    
    ring_supermode.putv("t_buffer", t_buffer)
    ring_supermode.eval(eta_sweep_script)

    nmodes = 4  # should match Lumerical trial modes

    mode_data = []

    for m in range(1, nmodes+1):
        mode_name = f"mode{m}"

        try:
            # --- basic properties ---
            neff = np.real(ring_supermode.getv(f"FDE::data::{mode_name}.neff"))
            TEfrac = ring_supermode.getv(f"FDE::data::{mode_name}.TE polarization fraction")
            loss = ring_supermode.getv(f"FDE::data::{mode_name}.loss")

            x = np.squeeze(ring_supermode.getv(f"FDE::data::{mode_name}.x"))
            y = np.squeeze(ring_supermode.getv(f"FDE::data::{mode_name}.y"))

            Ex = np.squeeze(ring_supermode.getv(f"FDE::data::{mode_name}.Ex"))
            Ey = np.squeeze(ring_supermode.getv(f"FDE::data::{mode_name}.Ey"))
            Ez = np.squeeze(ring_supermode.getv(f"FDE::data::{mode_name}.Ez"))

        except:
            print(f"WARNING: Mode {mode_name} not found, skipping...")
            continue  # skip missing modes safely

        # --- grids ---
        X, Y = np.meshgrid(x, y, indexing='ij')
        
        # --- intensity ---
        E2 = np.abs(Ex)**2 + np.abs(Ey)**2 + np.abs(Ez)**2
        
        # Masks
        margin = 20e-9

        mask_srn = (
            (X >= -W/2 + margin) & (X <= W/2 - margin) &
            (Y >= y_core_center - H/2 + margin) & (Y <= y_core_center + H/2 - margin)
        )

        mask_pcm = (
            (X >= W/2 + t_buffer) & (X <= W/2 + g) &
            (Y >= y_core_center - H/2 + margin) & (Y <= y_core_center + H/2 - margin)
        )

        # Energy
        E_total = np.sum(E2)
        E_srn   = np.sum(E2 * mask_srn)
        E_pcm   = np.sum(E2 * mask_pcm)

        eta_srn = E_srn / E_total
        eta_pcm = E_pcm / E_total

        neff = np.real(ring_supermode.getv(f"{mode_name}.neff"))

        mode_data.append({
            "mode": m,
            "neff": neff,
            "eta_srn": eta_srn,
            "eta_pcm": eta_pcm,
            "loss_dB_cm": loss_dB_cm,
            "TEfrac": TEfrac
        })
        
    # Select valid modes where SRN dominates PCM
    TE_threshold = 0.90

    valid_modes = [
        md for md in mode_data
        if (md["TEfrac"] > TE_threshold) and (md["eta_srn"] > md["eta_pcm"])
    ]

    if len(valid_modes) == 0:
        print("WARNING: No valid modes found")
        continue

    # Sort by SRN confinement strength (not neff!)
    srn_modes = sorted(valid_modes, key=lambda x: x["eta_srn"], reverse=True)
    
    # Pick the most SRN-like mode (for your current metric)
    best_mode = srn_modes[0]

    eta_pcm = best_mode["eta_pcm"]
    eta_good = 1 - eta_pcm
    loss_dB_cm = best_mode["loss_dB_cm"]

    print("====================================")
    print(f"Buffer thickness = {t_buffer*1e9:.1f} nm")
    print(f"Selected mode = {best_mode['mode']}")
    print(f"neff = {best_mode['neff']:.4f}")
    print(f"eta_srn = {best_mode['eta_srn']:.4f}")
    print(f"eta_pcm = {eta_pcm:.4f}")
    print(f"eta_good = {eta_good:.4f}")
    print("====================================")
    
    pcm_confinement_results.append(eta_pcm)
    good_confinement_results.append(eta_good)
    loss_results.append(loss_dB_cm)
    
# Plot all the results on the same figure
plt.figure(figsize=(10, 6))
plt.plot(t_buffer_values*1e9, pcm_confinement_results, label='PCM Confinement (eta_pcm)', marker='o')
plt.plot(t_buffer_values*1e9, good_confinement_results, label='Good Confinement (eta_good)', marker='o')
plt.xlabel('Buffer Thickness (nm)')
plt.title('Effect of Buffer Thickness on Confinement')
plt.legend()
plt.grid()

plt.figure(figsize=(10, 6))
plt.plot(t_buffer_values*1e9, loss_results, label='Loss (dB/cm)', marker='o', color='red')
plt.xlabel('Buffer Thickness (nm)')
plt.title('Effect of Buffer Thickness on Loss')
plt.legend()
plt.grid()
plt.show()