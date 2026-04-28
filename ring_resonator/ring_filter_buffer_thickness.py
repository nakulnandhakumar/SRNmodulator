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
    
for t_buffer in t_buffer_values:
    ring_supermode.putv("t_buffer", t_buffer)

    ring_supermode.eval(eta_sweep_script)

    # Get the mode profiles for the fundamental TE mode
    x = np.squeeze(ring_supermode.getv("x"))
    y = np.squeeze(ring_supermode.getv("y"))
    E2 = np.squeeze(ring_supermode.getv("E2"))

    X, Y = np.meshgrid(x, y, indexing='ij')
    
    loss_dB_cm = ring_supermode.getv("loss_TE_dB_cm")

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

    # ============================================================
    # Define masks
    # ============================================================
    margin = 20e-9  # 20 nm tolerance

    # SRN core region
    mask_srn = (
        (X >= -W/2 + margin) & (X <= W/2 - margin) &
        (Y >= y_core_center - H/2 + margin) & (Y <= y_core_center + H/2 - margin)
    )

    # PCM region (right side AFTER buffer)
    mask_pcm = (
        (X >= W/2 + t_buffer) & (X <= W/2 + g) &
        (Y >= y_core_center - H/2 + margin) & (Y <= y_core_center + H/2 - margin)
    )

    # ============================================================
    # Compute energy fractions
    # ============================================================
    E_total = np.sum(E2)
    E_pcm   = np.sum(E2 * mask_pcm)

    eta_pcm = E_pcm / E_total
    eta_good = 1 - eta_pcm

    print("====================================")
    print(f"Buffer thickness t_buffer = {t_buffer*1e9:.1f} nm")
    print(f"PCM confinement eta_pcm = {eta_pcm:.4f}")
    print(f"Good confinement eta_good = {eta_good:.4f}")
    print(f"Loss (dB/cm) = {loss_dB_cm:.4f}")
    print("====================================")