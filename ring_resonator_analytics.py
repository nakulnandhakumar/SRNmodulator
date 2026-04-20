import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import interp1d
from ring_resonator.sweep_kappa_vs_gap import sweep_kappa_vs_gap
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

dneff_active = 4.278e-06
static_dneff = 0.0014

alpha_roughness_dB_cm = 3
extra_loss_dB_cm = 7.539
alpha_active_dB_cm = 0.39982 + alpha_roughness_dB_cm + extra_loss_dB_cm
alpha_passive_dB_cm = 0 + alpha_roughness_dB_cm + extra_loss_dB_cm

Vdc = 667.1

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
# SWEEP GAP → EXTRACT κ′
# ============================================================
sweep_kappa_vs_gap(lambda0=lam0, gap_start=100e-9, gap_end=200e-9, Npoints=25, output_csv=f"ring_resonator/kappa({lam0*1e9:.0f}nmcritical)_vs_gap.csv")
df_kvg = pd.read_csv(f"ring_resonator/kappa({lam0*1e9:.0f}nmcritical)_vs_gap.csv")

# convert to ring coupling
kappa_prime_kvg = df_kvg["kappa_prime (1/m)"].values  
kappa_kvg = np.sin(kappa_prime_kvg * L_cpl)

# find optimal gap for critical coupling
idx = np.argmin(np.abs(kappa_kvg - kappa_target))
gaps_kvg = df_kvg["gap (m)"].values

g_opt = gaps_kvg[idx]
kappa_opt = kappa_kvg[idx]

print(f"\nOptimal gap for critical coupling at λ0 = {lam0*1e9:.2f} nm:")
print(f"  g_opt = {g_opt*1e9:.1f} nm")
print(f"  κ_opt = {kappa_opt:.4f}")

# ============================================================
# LOAD κ(λ) DATA FROM CSV (PANDAS)
# ============================================================
# Sweep λ at optimal gap to extract kappa(λ), neff_even(λ), neff_odd(λ)
sweep_kappa_vs_lambda(g_opt=g_opt, lambda_start=1.54e-6, lambda_end=1.56e-6, Npoints=100, output_csv=f"ring_resonator/kappa({lam0*1e9:.0f}nmcritical)_vs_lambda.csv")
df_kvl = pd.read_csv(f"ring_resonator/kappa({lam0*1e9:.0f}nmcritical)_vs_lambda.csv")

lambdas_kvl = df_kvl["lambda (m)"].values
kappa_prime_kvl = df_kvl["kappa_prime (1/m)"].values

# convert to κ(λ)
kappa_kvl = np.sin(kappa_prime_kvl * L_cpl)

# build interpolator
kappa_interp = interp1d(
    lambdas_kvl,
    kappa_kvl,
    kind='linear',
    fill_value="extrapolate"
)

# evaluate on dense wavelength grid
kappa_lam = kappa_interp(lam)

# compute t(λ)
t_lam = np.sqrt(1 - kappa_lam**2)

# ============================================================
# EFFECTIVE INDEX + GROUP INDEX
# ============================================================
ng_eff = (ng_active * L_active + ng_passive * L_passive) / L_ring

# unbiased
optical_path_unbiased = neff_active * L_active + neff_passive * L_passive

# DC-biased operating point
optical_path_bias = (neff_active + static_dneff) * L_active + neff_passive * L_passive

# DC + AC modulation
optical_path_mod = (neff_active + static_dneff + dneff_active) * L_active + neff_passive * L_passive

phi_unbiased = (2 * np.pi / lam) * optical_path_unbiased
phi_bias = (2 * np.pi / lam) * optical_path_bias
phi_mod = (2 * np.pi / lam) * optical_path_mod

# ============================================================
# TRANSMISSION
# ============================================================
def ring_through_transmission(t, a, phi):
    return np.abs((t - a * np.exp(-1j * phi)) / (1 - t * a * np.exp(-1j * phi)))**2

T_unbiased = ring_through_transmission(t_lam, a, phi_unbiased)
T_bias = ring_through_transmission(t_lam, a, phi_bias)
T_mod = ring_through_transmission(t_lam, a, phi_mod)

# ============================================================
# PLOT κ vs. GAP
# ============================================================
plt.figure()
plt.plot(gaps_kvg * 1e9, kappa_kvg, 'o-', label="κ(g) from supermode")
plt.axhline(kappa_target, linestyle='--', label="target κ") # mark optimal point
plt.scatter(g_opt * 1e9, kappa_opt, s=80)
plt.xlabel("Gap (nm)")
plt.ylabel("Coupling coefficient κ")
plt.title("Coupling vs Gap")
plt.grid(True)
plt.legend()
plt.show()

# ============================================================
# PLOT κ vs. λ
# ============================================================
plt.figure()
plt.plot(lambdas_kvl * 1e9, kappa_kvl, 'o', label="CSV data")
plt.plot(lam * 1e9, kappa_lam, '-', label="Linear Interp")
plt.xlabel("Wavelength (nm)")
plt.ylabel("kappa")
plt.legend()
plt.grid(True)
plt.show()

# ============================================================
# PLOT TRANSMISSION SPECTRUM of perturbed vs. static
# ============================================================
plt.figure()
plt.plot(lam * 1e9, T_unbiased, label="Unbiased")
plt.plot(lam * 1e9, T_bias, label="DC-biased")
plt.plot(lam * 1e9, T_mod, "--", label="DC + AC")
plt.xlabel("Wavelength (nm)")
plt.ylabel("Transmission")
plt.title("Ring Resonator")
plt.legend()
plt.grid()
plt.show()

# ============================================================
# EXTRACT NUMERICAL METRICS FROM SPECTRUM (CLEAN VERSION)
# ============================================================

# --- analytic FSR ---
FSR_analytic = lam0**2 / (ng_eff * L_ring)

# --- numeric FSR, linewidth, Q from spectrum ---
# Robust peak and dip finder for high-Q resonator spectra
def find_resonance_regions(T, lam, min_spacing_nm=0.5*FSR_analytic*1e9):
    raw_peaks = np.where((T[1:-1] > T[:-2]) & (T[1:-1] > T[2:]))[0] + 1

    if len(raw_peaks) < 2:
        return np.array([], dtype=int), np.array([], dtype=int)

    min_spacing = min_spacing_nm * 1e-9
    peaks = [raw_peaks[0]]

    for idx in raw_peaks[1:]:
        if lam[idx] - lam[peaks[-1]] >= min_spacing:
            peaks.append(idx)
        else:
            if T[idx] > T[peaks[-1]]:
                peaks[-1] = idx

    peaks = np.array(peaks, dtype=int)

    dips = []
    for i in range(len(peaks) - 1):
        left = peaks[i]
        right = peaks[i + 1]
        window = slice(left, right + 1)
        local_min = np.argmin(T[window])
        dips.append(left + local_min)

    return peaks, np.array(dips, dtype=int)

# --- find all local minima (resonances) ---
peak_indices, dip_indices = find_resonance_regions(T_bias, lam)
if len(dip_indices) < 2:
    raise RuntimeError("Not enough resonances found to compute FSR.")

# --- pick resonance closest to lam0 ---
center_dip_idx = np.argmin(np.abs(lam[dip_indices] - lam0))
center_idx = dip_indices[center_dip_idx]
lam_res = lam[center_idx]

print(f"Resonance found at λ = {lam_res*1e9:.4f} nm (index {center_idx})")

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
T_min = T_bias[center_idx]
print(f"Resonance depth (min transmission) = {T_min:.6f}")

# --- pick nearest peak on each side of resonance ---
left_peak_idx = peak_indices[center_dip_idx]
right_peak_idx = peak_indices[center_dip_idx + 1]

T_peak = 0.5 * (T_bias[left_peak_idx] + T_bias[right_peak_idx])
half_level = 0.5 * (T_peak + T_min)
print(f"Peak transmission = {T_peak:.6f}, Half level = {half_level:.6f}")

# left side crossing inside local window only
left_segment = T_bias[left_peak_idx:center_idx + 1]
left_cross_rel = np.where(left_segment > half_level)[0]
lam_left = lam[left_peak_idx + left_cross_rel[-1]] if len(left_cross_rel) > 0 else lam[center_idx]

# right side crossing inside local window only
right_segment = T_bias[center_idx:right_peak_idx + 1]
right_cross_rel = np.where(right_segment > half_level)[0]
lam_right = lam[center_idx + right_cross_rel[0]] if len(right_cross_rel) > 0 else lam[center_idx]

print(f"Left crossing at λ = {lam_left*1e9:.4f} nm, Right crossing at λ = {lam_right*1e9:.4f} nm")

# compute linewidth, Q
linewidth = lam_right - lam_left
Q_numeric = lam_res / linewidth

# compute bandwidth in GHz
c = 3e8
f_res = c / lam_res
bandwidth = f_res / Q_numeric

# ============================================================
# TRACK SAME RESONANCE FOR MODULATION SHIFT
# ============================================================
# use SAME peak-to-peak window from biased resonance
mod_window = slice(left_peak_idx, right_peak_idx + 1)

# find dip inside that SAME window
local_min_mod = np.argmin(T_mod[mod_window])
lam_res_mod = lam[left_peak_idx + local_min_mod]

# compute shift
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
print(f"Bandwidth       = {bandwidth/1e9:.3f} GHz")

print("\n--- Modulation ---")
print(f"AC Δλ shift       = {dlam_numeric*1e9:.4f} nm")
print(f"AC Δλ / linewidth = {dlam_numeric/linewidth:.3f}")

print("\n--- Extinction ---")
print(f"ER (static)    = {ER_static_dB:.2f} dB")

# ============================================================
# OPERATING POINT FROM LEFT-SIDE RESONANCE (NO MODIFICATION TO ABOVE CODE)
# ============================================================

print("\n========== OPERATING POINT SEARCH ==========")

# ------------------------------------------------------------
# 1. Find resonance strictly LEFT of λ0
# ------------------------------------------------------------
lam_dips = lam[dip_indices]

left_mask = lam_dips < lam0
if not np.any(left_mask):
    raise RuntimeError("No resonance found left of lambda0")

dip_indices_left = dip_indices[left_mask]

# closest resonance to λ0 but still on the left
left_dip_idx = dip_indices_left[np.argmin(np.abs(lam[dip_indices_left] - lam0))]
lam_res_left = lam[left_dip_idx]

print(f"Left resonance selected at λ = {lam_res_left*1e9:.4f} nm")

# ------------------------------------------------------------
# 2. Get its peak-to-peak window (reuse existing arrays)
# ------------------------------------------------------------
left_dip_list_idx = np.where(dip_indices == left_dip_idx)[0][0]

left_peak_left  = peak_indices[left_dip_list_idx]
right_peak_left = peak_indices[left_dip_list_idx + 1]

# ------------------------------------------------------------
# 3. Search RIGHT slope (because we shift right with DC bias)
# ------------------------------------------------------------
lam_candidates = lam[left_dip_idx:right_peak_left + 1]
T_bias_candidates = T_bias[left_dip_idx:right_peak_left + 1]
T_mod_candidates  = T_mod[left_dip_idx:right_peak_left + 1]

# ------------------------------------------------------------
# 4. Compute modulation metrics
# ------------------------------------------------------------
ER_mod_candidates_dB = 10 * np.log10(
    np.maximum(T_bias_candidates, T_mod_candidates) /
    np.minimum(T_bias_candidates, T_mod_candidates)
)

deltaT_candidates = np.abs(T_mod_candidates - T_bias_candidates)

# ------------------------------------------------------------
# 5. Add realism constraints
# ------------------------------------------------------------

# define ON and OFF states at each candidate point
T_on_candidates  = np.maximum(T_bias_candidates, T_mod_candidates)
T_off_candidates = np.minimum(T_bias_candidates, T_mod_candidates)

# require the "light goes through" state to be realistically high
T_on_min_allowed = 0.75

# optional: also reject absurdly tiny OFF states if desired
# set to 0.0 if you do not want to constrain OFF state
T_off_min_allowed = 1e-3

valid_mask = (
    (T_on_candidates >= T_on_min_allowed) &
    (T_off_candidates >= T_off_min_allowed)
)

if not np.any(valid_mask):
    raise RuntimeError(
        "No realistic operating point found: no point has ON-state transmission "
        f">= {T_on_min_allowed:.2f} within the allowed shift range."
    )

# ------------------------------------------------------------
# 6. Choose best operating point among valid ones
# ------------------------------------------------------------
ER_valid = ER_mod_candidates_dB.copy()
ER_valid[~valid_mask] = -np.inf

idx_opt = np.argmax(ER_valid)
lam_op = lam_candidates[idx_opt]

# ============================================================
# RECOMPUTE WITH SHIFTED DC BIAS
# ============================================================

# numerially compute required shift in resonance to align to λ0
dlam_needed = lam0 - lam_op
T_target = T_bias_candidates[idx_opt]
idx_1550 = np.argmin(np.abs(lam - lam0))

def compute_T1550(static_shift):
    optical_path = (neff_active + static_shift) * L_active + neff_passive * L_passive
    phi = (2 * np.pi / lam) * optical_path
    T = ring_through_transmission(t_lam, a, phi)
    return T[idx_1550], T

static_sweep = np.linspace(static_dneff - 0.02, static_dneff + 0.02, 200)

best_idx = None
best_error = np.inf

for i, sd in enumerate(static_sweep):
    T1550, _ = compute_T1550(sd)
    error = abs(T1550 - T_target)

    if error < best_error:
        best_error = error
        best_idx = i

static_dneff_target = static_sweep[best_idx]
dneff_needed_numeric = static_dneff_target - static_dneff
dneff_needed_analytic = (dlam_needed / lam0) * (ng_eff * L_ring) / L_active

# recompute optical paths and transmissions with this target static dneff
_, T_bias_new = compute_T1550(static_dneff_target)
optical_path_mod_new = (neff_active + static_dneff_target + dneff_active) * L_active + neff_passive * L_passive
phi_mod_new  = (2 * np.pi / lam) * optical_path_mod_new
T_mod_new  = ring_through_transmission(t_lam, a, phi_mod_new)

# extract metrics at lam_op
idx_1550 = np.argmin(np.abs(lam - lam0))

T_bias_1550 = T_bias_new[idx_1550]
T_mod_1550  = T_mod_new[idx_1550]

ER_mod_1550_dB = 10 * np.log10(
    max(T_bias_1550, T_mod_1550) /
    min(T_bias_1550, T_mod_1550)
)

deltaT_1550 = abs(T_mod_1550 - T_bias_1550)

# ============================================================
# STATIC ER AT 1550 (USING PEAK OF SAME RESONANCE)
# ============================================================

peaks_new, dips_new = find_resonance_regions(T_bias_new, lam)
center_idx_new = dips_new[np.argmin(np.abs(lam[dips_new] - lam0))]

dip_list_idx_new = np.where(dips_new == center_idx_new)[0][0]

left_peak_new  = peaks_new[dip_list_idx_new]
right_peak_new = peaks_new[dip_list_idx_new + 1]

T_min = T_bias_new[center_idx_new]
T_peak = 0.5 * (T_bias_new[left_peak_new] + T_bias_new[right_peak_new])

ER_static_1550_dB = 10 * np.log10(T_peak / T_min)

# ------------------------------------------------------------
# 7. Compute required DC shift to align λ_op → λ0
# ------------------------------------------------------------
print(f"\n--- Required Shift to Align to 1550 nm ---")
print(f"λ0                    = {lam0*1e9:.4f} nm")
print(f"Δλ needed             = {dlam_needed*1e9:.4f} nm")
print(f"Numeric Δneff         = {dneff_needed_numeric:.6e}")
print(f"Analytic Δneff        = {dneff_needed_analytic:.6e}")

# -------------------------------------------------------------
# 8. Print performance at 1550 nm with this DC shift applied
# -------------------------------------------------------------

print(f"\n--- Optimal Operating Point (SHIFTED TO 1550) ---")
print(f"λ_op (original)       = {lam_op*1e9:.4f} nm")
print(f"Δλ needed             = {dlam_needed*1e9:.4f} nm")

print(f"\n--- Performance at 1550 nm ---")
print(f"T_bias(1550)          = {T_bias_1550:.6f}")
print(f"T_mod(1550)           = {T_mod_1550:.6f}")
print(f"Modulation ER         = {ER_mod_1550_dB:.3f} dB")
print(f"Transmission swing    = {deltaT_1550:.6f}")

print(f"\n--- Static ER at 1550 ---")
print(f"ER_static             = {ER_static_1550_dB:.3f} dB")