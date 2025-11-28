import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# -------------------- user params --------------------
csv_path    = "dmitri_recreation/neff_coeffs.csv"      # your CSV filename
wavelength0 = 1550e-9                  # [m]
f_drive     = 10e9                     # cosine frequency [Hz]
sample_rate = 2000e9                    # sample rate [Hz]
n_cycles    = 2                        # number of cycles to simulate
Vpk         = 2.0                      # single amplitude [V]
# -----------------------------------------------------

# Load CSV
df = pd.read_csv(csv_path)

# Constants
c = 3e8
k0 = 2 * np.pi / wavelength0

# Generate time array
t = np.arange(0, n_cycles / f_drive, 1 / sample_rate)
v = Vpk * np.cos(2 * np.pi * f_drive * t)

# Compute Δn_eff(t) and phase change for each Vdc
plt.figure(figsize=(7, 5))
for _, row in df.iterrows():
    K0, K1, K2 = row["K0"], row["K1"], row["K2"]
    dneff_t = K1*v + K2*(v**2)     # Δn_eff(t) (no DC term)
    phi = k0 * dneff_t           # phase shift per meter (un-normalized)
    
    # # --- normalization ---
    phi_norm = phi / np.max(np.abs(phi))
    
    plt.plot(t * 1e12, phi_norm, label=f"Vdc={row['Vdc']} V")
        
# Ideal linear (no chirp): cosine wave
plt.plot(t*1e12, np.cos(2 * np.pi * f_drive * t), 'k--', label="Ideal linear")

plt.xlabel("Time (ns)")
plt.ylabel("Normalized phase change (Δφ per meter)")
plt.title(f"Normalized phase vs time at {f_drive/1e9:.1f} GHz, Vpk={Vpk} V")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()