import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import interp1d
from ring_resonator.sweep_kappa_vs_gap import sweep_kappa_vs_gap
from ring_resonator.sweep_kappa_vs_lambda import sweep_kappa_vs_lambda
from scipy.signal import find_peaks

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

# ============================================================
# Precompute kappa vs gap and kappa(λ) shape
# ============================================================

# first sweep kappa vs gap
# sweep_kappa_vs_gap(lambda0=lam0, gap_start=300e-9, gap_end=500e-9, Npoints=50, output_csv=f"ring_resonator/kappa({lam0*1e9:.0f}nmcritical)_vs_gap.csv")
df_kvg = pd.read_csv(f"ring_resonator/kappa({lam0*1e9:.0f}nmcritical)_vs_gap.csv")

kappa_prime_kvg = df_kvg["kappa_prime (1/m)"].values  
kappa_kvg = np.sin(kappa_prime_kvg * L_cpl)

# then sweep kappa vs wavelength at optimal gap for critical coupling
# sweep_kappa_vs_lambda(g_opt=g_opt, lambda_start=1.54e-6, lambda_end=1.56e-6, Npoints=100, output_csv=f"ring_resonator/kappa({lam0*1e9:.0f}nmcritical)_vs_lambda.csv")
df_kvl = pd.read_csv(f"ring_resonator/kappa({lam0*1e9:.0f}nmcritical)_vs_lambda.csv")
lambdas_kvl = df_kvl["lambda (m)"].values
kappa_prime_kvl = df_kvl["kappa_prime (1/m)"].values

kappa_kvl = np.sin(kappa_prime_kvl * L_cpl)

kappa_interp = interp1d(
    lambdas_kvl,
    kappa_kvl,
    kind='linear',
    fill_value="extrapolate"
)

# evaluate once on dense grid
kappa_ref = kappa_interp(lam)

# normalize at lambda0
idx0 = np.argmin(np.abs(lam - lam0))
kappa_ref_1550 = kappa_ref[idx0]

kappa_shape = kappa_ref / kappa_ref_1550

# ============================================================
# Sweep extra loss and compute performance metrics
# ============================================================
alpha_sweep_dB_cm = np.linspace(0, 20, 25)
results = []

for extra_loss in alpha_sweep_dB_cm:
    alpha_roughness_dB_cm = 3
    alpha_active_dB_cm = 0.39982 + alpha_roughness_dB_cm + extra_loss
    alpha_passive_dB_cm = 0 + alpha_roughness_dB_cm + extra_loss

    alpha_active = dBcm_to_nepers_per_m(alpha_active_dB_cm)
    alpha_passive = dBcm_to_nepers_per_m(alpha_passive_dB_cm)

    a = np.exp(-0.5 * (alpha_active * L_active + alpha_passive * L_passive))

    # ============================================================
    # TARGET COUPLING FOR CRITICAL COUPLING (at λ0)
    # ============================================================
    kappa_target = np.sqrt(1 - a**2)

    # find optimal gap for critical coupling
    idx = np.argmin(np.abs(kappa_kvg - kappa_target))
    gaps_kvg = df_kvg["gap (m)"].values

    g_opt = gaps_kvg[idx]
    kappa_opt = kappa_kvg[idx]

    # apply shape scaling to get kappa vs wavelength
    kappa_lam = kappa_target * kappa_shape
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
    # Find linewidth and Q
    # ============================================================

    # analytic FSR needed for resonance finding to find linewidth and Q
    FSR_analytic = lam0**2 / (ng_eff * L_ring)

    # Helper function to find resonance peaks and dips
    def find_resonance_regions(T, lam, FSR_analytic):
        # --------------------------------------------------
        # 1. Smooth slightly to remove numerical noise
        # --------------------------------------------------
        window = 51  # must be odd
        T_smooth = np.convolve(T, np.ones(window)/window, mode='same')

        # --------------------------------------------------
        # 2. Use prominence-based peak detection
        # --------------------------------------------------
        min_spacing = 0.5 * FSR_analytic

        # convert spacing to index distance
        dlam = lam[1] - lam[0]
        min_distance_pts = int(min_spacing / dlam)

        peaks, props = find_peaks(
            T_smooth,
            distance=min_distance_pts,
            prominence=1e-5  # tune if needed
        )

        # --------------------------------------------------
        # 3. If still not enough peaks → fallback
        # --------------------------------------------------
        if len(peaks) < 2:
            return np.array([], dtype=int), np.array([], dtype=int)

        # --------------------------------------------------
        # 4. Find dips between peaks (this part is good already)
        # --------------------------------------------------
        dips = []
        for i in range(len(peaks) - 1):
            left = peaks[i]
            right = peaks[i + 1]
            local_min = np.argmin(T[left:right+1])
            dips.append(left + local_min)

        return peaks, np.array(dips)

    # --- find all local minima (resonances) ---
    peak_indices, dip_indices = find_resonance_regions(T_bias, lam)
    if len(dip_indices) < 2:
        raise RuntimeError("Not enough resonances found to compute FSR.")

    # --- pick resonance closest to lam0 ---
    center_dip_idx = np.argmin(np.abs(lam[dip_indices] - lam0))
    center_idx = dip_indices[center_dip_idx]
    lam_res = lam[center_idx]

    # --- linewidth (FWHM) ---
    T_min = T_bias[center_idx]

    # --- pick nearest peak on each side of resonance ---
    left_peak_idx = peak_indices[center_dip_idx]
    right_peak_idx = peak_indices[center_dip_idx + 1]

    T_peak = 0.5 * (T_bias[left_peak_idx] + T_bias[right_peak_idx])
    half_level = 0.5 * (T_peak + T_min)

    # left side crossing inside local window only
    left_segment = T_bias[left_peak_idx:center_idx + 1]
    left_cross_rel = np.where(left_segment > half_level)[0]
    lam_left = lam[left_peak_idx + left_cross_rel[-1]] if len(left_cross_rel) > 0 else lam[center_idx]

    # right side crossing inside local window only
    right_segment = T_bias[center_idx:right_peak_idx + 1]
    right_cross_rel = np.where(right_segment > half_level)[0]
    lam_right = lam[center_idx + right_cross_rel[0]] if len(right_cross_rel) > 0 else lam[center_idx]

    # compute linewidth, Q
    linewidth = lam_right - lam_left
    Q_numeric = lam_res / linewidth

    # compute bandwidth in GHz
    c = 3e8
    f_res = c / lam_res
    bandwidth = f_res / Q_numeric
    
    results.append({
        "extra_loss_dB_cm": extra_loss,
        "Q_numeric": Q_numeric,
        "linewidth_nm": linewidth * 1e9,
        "bandwidth_GHz": bandwidth / 1e9
    })
    
df_results = pd.DataFrame(results)

loss = df_results["extra_loss_dB_cm"].values
Q_vals = df_results["Q_numeric"].values
linewidth_vals = df_results["linewidth_nm"].values
BW_vals = df_results["bandwidth_GHz"].values


# Build interpolation function: BW(loss)
f_loss_from_bw = interp1d(
    BW_vals,
    loss,
    kind='linear',
    fill_value="extrapolate"
)

loss_required_10GHz = float(f_loss_from_bw(10))
loss_required_20GHz = float(f_loss_from_bw(20))

print(f"\n=== Required Loss for ~10 GHz ===")
print(f"Extra loss required ≈ {loss_required_10GHz:.3f} dB/cm")

print(f"\n=== Required Loss for ~20 GHz ===")
print(f"Extra loss required ≈ {loss_required_20GHz:.3f} dB/cm")

plt.figure()
plt.plot(loss, BW_vals, 'o-')
plt.axhline(10, linestyle='--')  # target 10 GHz
plt.axhline(20, linestyle='--')  # target 20 GHz
plt.xlabel("Extra Loss (dB/cm)")
plt.ylabel("Bandwidth (GHz)")
plt.title("Bandwidth vs Extra Loss")
plt.grid(True)
plt.show()