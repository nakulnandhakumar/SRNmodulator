import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi # pyright: ignore[reportMissingImports]
import pandas as pd
from scipy.interpolate import interp1d
from ring_resonator.sweep_kappa_vs_lambda import sweep_kappa_vs_lambda

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
# WAVELENGTH SWEEP
# ============================================================
lam = np.linspace(1.54e-6, 1.56e-6, 1000000)
lam0 = 1.55e-6

# ============================================================
# LOSS MODEL
# ============================================================
def dBcm_to_nepers_per_m(alpha_dB_cm):
    return alpha_dB_cm * 100 / (10 * np.log10(np.e))

alpha_active = dBcm_to_nepers_per_m(alpha_active_dB_cm)
alpha_passive = dBcm_to_nepers_per_m(alpha_passive_dB_cm)

a = np.exp(-0.5 * (alpha_active * L_active + alpha_passive * L_passive))

# ============================================================
# TARGET COUPLING FOR CRITICAL COUPLING (at λ0)
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
gaps = np.linspace(400e-9, 500e-9, 60)
kappa_prime_list = []
ring_supermode.putv("lambda", lam0) # set wavelength in MODE session

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

# ============================================================
# LOAD κ(λ) DATA FROM CSV (PANDAS)
# ============================================================
# Sweep λ at optimal gap to extract kappa(λ), neff_even(λ), neff_odd(λ)

# sweep_kappa_vs_lambda(g_opt=g_opt)
df = pd.read_csv("kappa_vs_lambda.csv")

lam_data = df["lambda (m)"].values
kappa_prime_data = df["kappa_prime (1/m)"].values

# convert to κ(λ)
kappa_data = np.sin(kappa_prime_data * L_cpl)

# build interpolator
kappa_interp = interp1d(
    lam_data,
    kappa_data,
    kind='cubic',
    fill_value="extrapolate"
)

# evaluate on dense wavelength grid
kappa_lambda = kappa_interp(lam)

# compute t(λ)
t_lambda = np.sqrt(1 - kappa_lambda**2)

# ============================================================
# EFFECTIVE INDEX + GROUP INDEX
# ============================================================
ng_eff = (ng_active * L_active + ng_passive * L_passive) / L_ring

optical_path_static = neff_active * L_active + neff_passive * L_passive
optical_path_mod = (neff_active + dneff_active) * L_active + neff_passive * L_passive

phi_static = (2 * np.pi / lam) * optical_path_static
phi_mod = (2 * np.pi / lam) * optical_path_mod

# ============================================================
# TRANSMISSION
# ============================================================
def ring_through_transmission(t, a, phi):
    return np.abs((t - a * np.exp(-1j * phi)) / (1 - t * a * np.exp(-1j * phi)))**2

T_static = ring_through_transmission(t_lambda, a, phi_static)
T_mod = ring_through_transmission(t_lambda, a, phi_mod)

# ============================================================
# EXTRACT NUMERICAL METRICS FROM SPECTRUM (CLEAN VERSION)
# ============================================================

# --- find all local minima (resonances) ---
dip_indices = np.where(
    (T_static[1:-1] < T_static[:-2]) &
    (T_static[1:-1] < T_static[2:])
)[0] + 1

if len(dip_indices) < 2:
    raise RuntimeError("Not enough resonances found to compute FSR.")

# --- pick resonance closest to lam0 ---
center_idx = dip_indices[np.argmin(np.abs(lam[dip_indices] - lam0))]
lam_res = lam[center_idx]

# --- FSR (distance between adjacent dips) ---
dip_positions = lam[dip_indices]

# find index of chosen dip in dip list
i_center = np.where(dip_indices == center_idx)[0][0]

if i_center == 0:
    FSR_numeric = dip_positions[1] - dip_positions[0]
elif i_center == len(dip_positions) - 1:
    FSR_numeric = dip_positions[-1] - dip_positions[-2]
else:
    FSR_numeric = 0.5 * (
        (dip_positions[i_center] - dip_positions[i_center - 1]) +
        (dip_positions[i_center + 1] - dip_positions[i_center])
    )

# --- linewidth (FWHM) ---
T_min = T_static[center_idx]

# find surrounding peaks
def find_local_maxima(y):
    return np.where((y[1:-1] > y[:-2]) & (y[1:-1] > y[2:]))[0] + 1

peak_indices = find_local_maxima(T_static)

# --- separate left and right of resonance ---
left_peaks = peak_indices[peak_indices < center_idx]
right_peaks = peak_indices[peak_indices > center_idx]

# --- pick nearest peak on each side ---
if len(left_peaks) == 0 or len(right_peaks) == 0:
    raise RuntimeError("Could not find peaks around resonance")

left_peak_idx = left_peaks[-1]      # closest on left
right_peak_idx = right_peaks[0]     # closest on right

T_peak = 0.5 * (T_static[left_peak_idx] + T_static[right_peak_idx])
half_level = 0.5 * (T_peak + T_min)

# find left crossing
left_cross = np.where(T_static[:center_idx] > half_level)[0]
lam_left = lam[left_cross[-1]] if len(left_cross) > 0 else lam[center_idx]

# find right crossing
right_cross = np.where(T_static[center_idx:] > half_level)[0]
lam_right = lam[center_idx + right_cross[0]] if len(right_cross) > 0 else lam[center_idx]

linewidth = lam_right - lam_left
Q_numeric = lam_res / linewidth

# --- analytic FSR ---
FSR_analytic = lam0**2 / (ng_eff * L_ring)

# ============================================================
# TRACK SAME RESONANCE FOR MODULATION SHIFT
# ============================================================
dip_indices_mod = np.where(
    (T_mod[1:-1] < T_mod[:-2]) &
    (T_mod[1:-1] < T_mod[2:])
)[0] + 1

lam_dips_mod = lam[dip_indices_mod]

# pick closest dip to original resonance
lam_res_mod = lam_dips_mod[np.argmin(np.abs(lam_dips_mod - lam_res))]

dlam_numeric = lam_res_mod - lam_res

# --- analytic shift ---
dlam_analytic = lam0 * (dneff_active * L_active) / (ng_eff * L_ring)

# ============================================================
# Q FACTORS (Analytic)
# ============================================================
kappa0 = kappa_interp(lam0)
Qc = (2 * np.pi * L_ring * ng_eff) / (lam0 * (-np.log(1 - kappa0**2)))

alpha_avg = (alpha_active * L_active + alpha_passive * L_passive) / L_ring
Qint = (2 * np.pi * ng_eff) / (alpha_avg * lam0)

Qtotal = 1 / (1 / Qc + 1 / Qint)

# ============================================================
# EXTINCTION RATIO
# ============================================================
ER_static_dB = 10 * np.log10(T_peak / T_min)

# ============================================================
# BANDWIDTH CALCULATION
# ============================================================
c = 3e8
f_res = c / lam_res
bandwidth = f_res / Q_numeric

# ============================================================
# PRINT RESULTS
# ============================================================
print("\n========== FINAL RING PERFORMANCE ==========")

print("\n--- Coupling ---")
print(f"Target κ       = {kappa_target:.4f}")
print(f"Optimal gap    = {g_opt*1e9:.2f} nm")
print(f"κ (at lambda0) = {kappa0:.4f}")

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