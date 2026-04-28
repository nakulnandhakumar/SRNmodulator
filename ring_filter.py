import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]

# ============================================================
# Plot the n and k data for the SBS amorphous phase change material
# ============================================================

# Read the CSV file
df = pd.read_csv("ring_resonator/n_k_sbs.csv")

# Plot n and k vs wavelength
plt.figure(figsize=(12, 5))
plt.plot(df["wavelength"] * 1e9, df["n_amorphous"], label="n (amorphous)")
plt.plot(df["wavelength"] * 1e9, df["n_crystalline"], label="n (crystalline)")
plt.plot(df["wavelength"] * 1e9, df["k_amorphous"], label="k (amorphous)")
plt.plot(df["wavelength"] * 1e9, df["k_crystalline"], label="k (crystalline)")
plt.xlabel("Wavelength (nm)")
plt.ylabel("Refractive Index (n) / Extinction Coefficient (k)")
plt.title("Refractive Index and Extinction Coefficient vs Wavelength")
plt.legend()
plt.grid()
# plt.show()

# Initialize Lumerical MODE for the ring filter waveguide
ring_supermode = lumapi.MODE(
            hide=False,
            project=r"./lumerical/mode/ring_supermode.lms"
        )

# ============================================================
# Sweep buffer thickness and observe mode profiles
# ============================================================

with open(r"./lumerical/mode/ring_filter_waveguide_run.lsf") as f:
    eta_sweep_script = f.read()
    
t_buffer = 150e-9

material_params = {
    "core_material_mode": "SRN 3.1 (Silicon Rich Nitride)",
    "clad_left_material": "SiO2 (Glass) - Palik",
    "clad_right_material": "SBS Amorphous",
    "BOX_cladding_material_mode": "SiO2 (Glass) - Palik",
}

for param, value in material_params.items():
    ring_supermode.putv(param, value)
    
ring_supermode.putv("t_buffer", t_buffer)

ring_supermode.eval(eta_sweep_script)

# Get the mode profiles for the fundamental TE mode
x = np.squeeze(ring_supermode.getv("x"))
y = np.squeeze(ring_supermode.getv("y"))
E2 = np.squeeze(ring_supermode.getv("E2"))

X, Y = np.meshgrid(x, y, indexing='ij')

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

# SRN core region
mask_srn = (
    (X >= -W/2) & (X <= W/2) &
    (Y >= y_core_center - H/2) & (Y <= y_core_center + H/2)
)

# PCM region (right side AFTER buffer)
mask_pcm = (
    (X >= W/2 + t_buffer) & (X <= W/2 + g) &
    (Y >= y_core_center - H/2) & (Y <= y_core_center + H/2)
)

# ============================================================
# Compute energy fractions
# ============================================================

E_total = np.sum(E2)
E_srn   = np.sum(E2 * mask_srn)
E_pcm   = np.sum(E2 * mask_pcm)

eta_srn = E_srn / E_total
eta_pcm = E_pcm / E_total
eta_other = 1 - eta_srn - eta_pcm

print("====================================")
print("SRN confinement eta_srn =", eta_srn)
print("PCM confinement eta_pcm =", eta_pcm)
print("Other energy            =", eta_other)
print("====================================")