import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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

# ============================================================
# RACETRACK GEOMETRY
# ============================================================
R = 20e-6
L_cpl = 3e-6
L_straight_total = 2 * L_cpl

L_ring = 2 * np.pi * R + L_straight_total
L_active = L_ring - L_cpl
L_passive = L_cpl

# ============================================================
# MODE / DEVICE PARAMETERS (AMORPHOUS PMC)
# ============================================================
neff_active = 2.4309
neff_passive = 2.2659

ng_active = 3.3753
ng_passive = 3.69967

alpha_roughness_dB_cm = 3
active_loss = 0         # ring filter has no modulating region
passive_loss = 0        # coupling region loss is passive loss
alpha_active_dB_cm = active_loss + alpha_roughness_dB_cm
alpha_passive_dB_cm = passive_loss + alpha_roughness_dB_cm