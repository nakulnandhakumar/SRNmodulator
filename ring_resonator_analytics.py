import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]

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
# MODE / DEVICE PARAMETERS
# ============================================================
neff_active = 2.4309
neff_passive = 2.2659

ng_active = 3.3753
ng_passive = 3.69967

dneff_active = 4.298e-06

alpha_active_dB_cm = 0.39982
alpha_passive_dB_cm = 0

# ============================================================
# LOSS MODEL
# ============================================================
def dBcm_to_nepers_per_m(alpha_dB_cm):
    return alpha_dB_cm * 100 / (10 * np.log10(np.e))

alpha_active = dBcm_to_nepers_per_m(alpha_active_dB_cm)
alpha_passive = dBcm_to_nepers_per_m(alpha_passive_dB_cm)

a = np.exp(-0.5 * (alpha_active * L_active + alpha_passive * L_passive))

# ============================================================
# TARGET COUPLING (CRITICAL)
# ============================================================
kappa_target = np.sqrt(1 - a**2)

# ============================================================
# LUMERICAL SESSION
# ============================================================
ring_supermode = lumapi.MODE(hide=False, project=r"./lumerical/mode/modulator_mode.lms")

with open(r"./lumerical/mode/ring_supermode.lsf") as f:
    lsf_script = f.read()

# ============================================================
# SWEEP GAP → EXTRACT κ′
# ============================================================
gaps = np.linspace(400e-9, 600e-9, 50)

kappa_prime_list = []

for g in gaps:
    print(f"\nRunning gap = {g*1e9:.1f} nm")

    ring_supermode.putv("g", g)
    ring_supermode.eval(lsf_script)

    kappa_prime = ring_supermode.getv("kappa_prime")
    kappa_prime_list.append(kappa_prime)

# ============================================================
# CONVERT TO ARRAYS
# ============================================================
gaps = np.array(gaps)
kappa_prime_array = np.array(kappa_prime_list)

# convert to ring coupling
kappa_array = np.sin(kappa_prime_array * L_cpl)

# ============================================================
# FIND OPTIMAL GAP (CRITICAL COUPLING)
# ============================================================
idx = np.argmin(np.abs(kappa_array - kappa_target))

g_opt = gaps[idx]
kappa_opt = kappa_array[idx]

print("\n====== CRITICAL COUPLING RESULT ======")
print(f"Target κ       = {kappa_target:.4f}")
print(f"Optimal gap    = {g_opt*1e9:.2f} nm")
print(f"κ at gap       = {kappa_opt:.4f}")

# ============================================================
# USE OPTIMAL κ FOR RING SIMULATION
# ============================================================
kappa = kappa_opt
t = np.sqrt(1 - kappa**2)

# ============================================================
# EFFECTIVE INDEX + GROUP INDEX
# ============================================================
ng_eff = (ng_active * L_active + ng_passive * L_passive) / L_ring

optical_path_static = neff_active * L_active + neff_passive * L_passive
optical_path_mod = (neff_active + dneff_active) * L_active + neff_passive * L_passive

# ============================================================
# WAVELENGTH SWEEP
# ============================================================
lam = np.linspace(1.54e-6, 1.56e-6, 1000000)
lam0 = 1.55e-6

phi_static = (2 * np.pi / lam) * optical_path_static
phi_mod = (2 * np.pi / lam) * optical_path_mod

# ============================================================
# TRANSMISSION
# ============================================================
def ring_through_transmission(t, a, phi):
    return np.abs((t - a * np.exp(-1j * phi)) / (1 - t * a * np.exp(-1j * phi)))**2

T_static = ring_through_transmission(t, a, phi_static)
T_mod = ring_through_transmission(t, a, phi_mod)

# ============================================================
# EXTRACT NUMERICAL METRICS FROM SPECTRUM
# ============================================================

# --- Resonance location ---
idx_min = np.argmin(T_static)
lam_res = lam[idx_min]

# --- Find peaks on either side for FSR ---
left = T_static[:idx_min]
right = T_static[idx_min:]

idx_left_max = np.argmax(left)
idx_right_max = np.argmax(right)

lam_left = lam[idx_left_max]
lam_right = lam[idx_min + idx_right_max]

FSR_numeric = lam_right - lam_left

# --- Linewidth (FWHM) ---
T_min = T_static[idx_min]
T_max = np.max(T_static)
half_level = (T_max + T_min) / 2

indices = np.where(T_static < half_level)[0]
valid = indices[(indices > idx_left_max) & (indices < idx_min + idx_right_max)]

if len(valid) > 2:
    lam_low = lam[valid[0]]
    lam_high = lam[valid[-1]]
    linewidth = lam_high - lam_low
else:
    linewidth = np.nan

# --- Q from spectrum ---
Q_numeric = lam_res / linewidth if linewidth != 0 else np.nan

# --- Analytic FSR ---
FSR_analytic = lam0**2 / (ng_eff * L_ring)

# --- Delta lambda (shift) ---
idx_min_mod = np.argmin(T_mod)
lam_res_mod = lam[idx_min_mod]
dlam_numeric = lam_res_mod - lam_res

# ============================================================
# Q FACTORS (Analytic)
# ============================================================
Qc = (2 * np.pi * ng_eff * R) / (lam0 * (-np.log(1 - kappa**2)))

alpha_avg = (alpha_active * L_active + alpha_passive * L_passive) / L_ring
Qint = (2 * np.pi * ng_eff) / (alpha_avg * lam0)

Qtotal = 1 / (1 / Qc + 1 / Qint)

# ============================================================
# EXTINCTION RATIO
# ============================================================
ER_static_dB = 10 * np.log10(np.max(T_static) / np.min(T_static))
ER_mod_dB = 10 * np.log10(np.max(T_mod) / np.min(T_mod))

# ============================================================
# PRINT RESULTS
# ============================================================
print("\n========== FINAL RING PERFORMANCE ==========")

print("\n--- Coupling ---")
print(f"Target κ       = {kappa_target:.4f}")
print(f"Optimal gap    = {g_opt*1e9:.2f} nm")
print(f"κ (used)       = {kappa:.4f}")

print("\n--- Q Factors (Analytic) ---")
print(f"Qc             = {Qc:.3e}")
print(f"Qint           = {Qint:.3e}")
print(f"Qtotal         = {Qtotal:.3e}")

print("\n--- Spectrum Metrics (Numeric) ---")
print(f"Resonance λ    = {lam_res*1e9:.4f} nm")
print(f"FSR (numeric)  = {FSR_numeric*1e9:.4f} nm")
print(f"FSR (analytic) = {FSR_analytic*1e9:.4f} nm")
print(f"Linewidth      = {linewidth*1e9:.4f} nm")
print(f"Q (numeric)    = {Q_numeric:.3e}")

print("\n--- Modulation ---")
print(f"Δλ shift       = {dlam_numeric*1e9:.4f} nm")
print(f"Δλ / linewidth = {dlam_numeric/linewidth:.3f}")

print("\n--- Extinction ---")
print(f"ER (static)    = {ER_static_dB:.2f} dB")
print(f"ER (mod)       = {ER_mod_dB:.2f} dB")

# ============================================================
# PLOT κ vs. GAP
# ============================================================
plt.figure()
plt.plot(gaps * 1e9, kappa_array, 'o-', label="κ(g) from supermode")
plt.axhline(kappa_target, linestyle='--', label="target κ") # mark optimal point
plt.scatter(g_opt * 1e9, kappa_opt, s=80)
plt.xlabel("Gap (nm)")
plt.ylabel("Coupling coefficient κ")
plt.title("Coupling vs Gap")
plt.grid(True)
plt.legend()
plt.show()

# ============================================================
# PLOT TRANSMISSION SPECTRUM of perturbed vs. static
# ============================================================
plt.figure()
plt.plot(lam * 1e9, T_static, label="Static")
plt.plot(lam * 1e9, T_mod, "--", label="Perturbed")
plt.xlabel("Wavelength (nm)")
plt.ylabel("Transmission")
plt.title("Ring Resonator")
plt.legend()
plt.grid()
plt.show()