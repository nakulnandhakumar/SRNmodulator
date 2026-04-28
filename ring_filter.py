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

# find peak of field (this is your true mode center)
ix, iy = np.unravel_index(np.argmax(E2), E2.shape)

x_center = x[ix]
y_center = y[iy]

print("Detected mode center:", x_center, y_center)

mask_srn = (
    (X >= x_center-W/2) & (X <= x_center+W/2) &
    (Y >= y_center - H/2) & (Y <= y_center + H/2)
)

# PCM region (right side AFTER buffer)
mask_pcm = (
    (X >= x_center + W/2 + t_buffer) & (X <= x_center + W/2 + g) &
    (Y >= y_center - H/2) & (Y <= y_center + H/2)
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

plt.figure(figsize=(6,5))

# field
plt.imshow(E2.T, origin='lower')

# SRN mask as black dots
ys, xs = np.where(mask_srn.T)
plt.scatter(xs, ys, s=2, c='black', alpha=0.6, label='SRN')

# PCM mask as red dots
ys, xs = np.where(mask_pcm.T)
plt.scatter(xs, ys, s=2, c='red', alpha=0.6, label='PCM')

plt.legend()
plt.title("E2 with mask points")
plt.show()