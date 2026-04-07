import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# INPUTS FROM FDTD
# ============================================================
P_bus = 0.585
P_ring = 0.20
Lc_fdtd = 8e-6          # straight coupler interaction length used in FDTD
L_cpl_ring = 5e-6       # effective coupling length in actual ring coupler region

# ============================================================
# RING GEOMETRY
# ============================================================
R = 20e-6               # ring radius [m]
L_ring = 2 * np.pi * R

# Piecewise segmentation
# Example: mostly active ring, small passive coupler section
L_active = L_ring - L_cpl_ring
L_passive = L_cpl_ring

# ============================================================
# MODE / DEVICE PARAMETERS
# Non-dispersive approximation for now
# ============================================================
neff_active = 2.4309
neff_passive = 2.2659

ng_active = 3.3753
ng_passive = 3.699251

dneff_active = 

alpha_active_dB_cm = 0.39982
alpha_passive_dB_cm = 0.00726

# ============================================================
# WAVELENGTH SWEEP
# ============================================================
lam = np.linspace(1.50e-6, 1.60e-6, 4000)

# ============================================================
# 1) EXTRACT COUPLING FROM FDTD
# ============================================================
# Normalize guided power from the two extracted modal powers
P_total_guided = P_bus + P_ring
P_ring_norm = P_ring / P_total_guided
P_bus_norm = P_bus / P_total_guided

# Coupling coefficient per unit length in straight coupler
kappa_prime = np.arcsin(np.sqrt(P_ring_norm)) / Lc_fdtd

# Dimensionless ring coupling coefficient from effective ring coupler length
kappa = np.sin(kappa_prime * L_cpl_ring)
t = np.sqrt(1 - kappa**2)

# ============================================================
# 2) EFFECTIVE GROUP INDEX
# ============================================================
ng_eff = (ng_active * L_active + ng_passive * L_passive) / L_ring

# ============================================================
# 3) PIECEWISE ROUND-TRIP EFFECTIVE INDEX
# ============================================================
# Static round-trip optical path
optical_path_static = neff_active * L_active + neff_passive * L_passive

# Perturbed round-trip optical path
optical_path_mod = (neff_active + dneff_active) * L_active + neff_passive * L_passive

# Equivalent average neff if you want to print it
neff_eff_static = optical_path_static / L_ring
neff_eff_mod = optical_path_mod / L_ring

# ============================================================
# 4) LOSS MODEL
# ============================================================
def dBcm_to_nepers_per_m(alpha_dB_cm):
    # power loss conversion
    return alpha_dB_cm * 100 / (10 * np.log10(np.e))

alpha_active = dBcm_to_nepers_per_m(alpha_active_dB_cm)
alpha_passive = dBcm_to_nepers_per_m(alpha_passive_dB_cm)

# Piecewise round-trip amplitude attenuation
a = np.exp(-0.5 * (alpha_active * L_active + alpha_passive * L_passive))

# ============================================================
# 5) RING PHASE
# ============================================================
phi_static = (2 * np.pi / lam) * optical_path_static
phi_mod = (2 * np.pi / lam) * optical_path_mod

# ============================================================
# 6) THROUGH-PORT TRANSMISSION
# ============================================================
def ring_through_transmission(t, a, phi):
    return np.abs((t - a * np.exp(-1j * phi)) / (1 - t * a * np.exp(-1j * phi)))**2

T_static = ring_through_transmission(t, a, phi_static)
T_mod = ring_through_transmission(t, a, phi_mod)

# ============================================================
# 7) WAVELENGTH SHIFT ESTIMATE
# ============================================================
# Small-signal estimate using effective group index
dlam_est = (lam.mean() / ng_eff) * dneff_active * (L_active / L_ring)

# Numerically extracted resonance shift from the nearest dip
idx_static = np.argmin(T_static)
idx_mod = np.argmin(T_mod)
lam_res_static = lam[idx_static]
lam_res_mod = lam[idx_mod]
dlam_numeric = lam_res_mod - lam_res_static

# ============================================================
# 8) Q ESTIMATES
# ============================================================
# Coupling Q (general formula)
Qc = (2 * np.pi * ng_eff * R) / (lam.mean() * (-np.log(1 - kappa**2)))

# Intrinsic Q
alpha_avg = (alpha_active * L_active + alpha_passive * L_passive) / L_ring
Qint = (2 * np.pi * ng_eff) / (alpha_avg * lam.mean())

# Loaded Q
Qtotal = 1 / (1 / Qc + 1 / Qint)

# ============================================================
# 9) EXTINCTION RATIO
# ============================================================
ER_static_dB = 10 * np.log10(np.max(T_static) / np.min(T_static))
ER_mod_dB = 10 * np.log10(np.max(T_mod) / np.min(T_mod))

# ============================================================
# 10) PRINT RESULTS
# ============================================================
print("========== COUPLER EXTRACTION ==========")
print(f"P_bus (raw modal)           = {P_bus:.6f}")
print(f"P_ring (raw modal)          = {P_ring:.6f}")
print(f"P_bus_norm                  = {P_bus_norm:.6f}")
print(f"P_ring_norm                 = {P_ring_norm:.6f}")
print(f"kappa_prime [1/m]           = {kappa_prime:.6e}")
print(f"kappa (dimensionless)       = {kappa:.6f}")
print(f"t (self-coupling)           = {t:.6f}")

print("\n========== EFFECTIVE INDICES ==========")
print(f"neff_eff_static             = {neff_eff_static:.6f}")
print(f"neff_eff_mod                = {neff_eff_mod:.6f}")
print(f"ng_eff                      = {ng_eff:.6f}")

print("\n========== SHIFT ==========")
print(f"Estimated dlam [nm]         = {dlam_est * 1e9:.6f}")
print(f"Numeric dlam from dips [nm] = {dlam_numeric * 1e9:.6f}")

print("\n========== Q VALUES ==========")
print(f"Qc                          = {Qc:.6e}")
print(f"Qint                        = {Qint:.6e}")
print(f"Qtotal                      = {Qtotal:.6e}")

print("\n========== EXTINCTION ==========")
print(f"ER_static [dB]              = {ER_static_dB:.4f}")
print(f"ER_mod [dB]                 = {ER_mod_dB:.4f}")

# ============================================================
# 11) PLOTS
# ============================================================
plt.figure(figsize=(8, 5))
plt.plot(lam * 1e9, T_static, label="Static")
plt.plot(lam * 1e9, T_mod, "--", label="Perturbed")
plt.xlabel("Wavelength (nm)")
plt.ylabel("Through transmission")
plt.title("Ring Resonator Transmission (Piecewise neff Model)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()