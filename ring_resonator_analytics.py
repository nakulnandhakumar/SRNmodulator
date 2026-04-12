import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]

# ============================================================
# RACETRACK GEOMETRY
# ============================================================
R = 10e-6
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
gaps = np.linspace(100e-9, 400e-9, 20)

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
lam = np.linspace(1.50e-6, 1.60e-6, 400000)
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
# Q FACTORS
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
print(f"Qc     = {Qc:.3e}")
print(f"Qint   = {Qint:.3e}")
print(f"Qtotal = {Qtotal:.3e}")
print(f"ER     = {ER_static_dB:.2f} dB")

# ============================================================
# PLOT κ vs. GAP
# ============================================================
plt.figure()
plt.plot(gaps * 1e9, kappa_array, 'o-', label="κ(g) from supermode")
plt.axhline(kappa_target, linestyle='--', label="critical κ")
# mark optimal point
plt.scatter(g_opt * 1e9, kappa_opt, s=80, label="optimal gap")
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