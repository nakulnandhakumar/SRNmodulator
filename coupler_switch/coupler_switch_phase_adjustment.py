import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
from scipy.optimize import curve_fit

df = pd.read_csv("coupler_switch/coupler_switch_wg_coupling_sweep.csv")

y_um = df["y_vertical_um"].values
kappa = df["kappa_per_m"].values

# Use only clean region before mode-tracking gets weird
clean = (y_um >= 0.0) & (y_um <= 0.9)

y_clean = y_um[clean]
k_clean = kappa[clean]

# Smooth interpolation over measured region
k_interp = PchipInterpolator(y_clean, k_clean)

# Fit exponential tail over final clean segment
tail_fit = (y_clean >= 0.55) & (y_clean <= 0.9)

def exp_tail(y, A, b):
    return A * np.exp(-b * y)

popt, _ = curve_fit(exp_tail, y_clean[tail_fit], k_clean[tail_fit], p0=[1e5, 5])

A_fit, b_fit = popt

def kappa_model(y_um):
    y_um = np.asarray(y_um)
    k = np.zeros_like(y_um, dtype=float)

    measured = y_um <= 0.9
    tail = y_um > 0.9

    k[measured] = k_interp(y_um[measured])

    # continuous tail after 0.9 um
    k_09 = k_interp(0.9)
    k[tail] = k_09 * np.exp(-b_fit * (y_um[tail] - 0.9))

    return k

# =====================
# BEND GEOMETRY
# =====================

R = 15e-6  # bend radius in meters
kappa_threshold = 100  # 1/m, stop once coupling is negligible
s_max = R * np.pi / 2  # Full quarter bend arc length

s = np.linspace(0, s_max, 2000)

# Pull-away displacement from circular bend
d_m = R * (1 - np.cos(s / R))
d_um_path = d_m * 1e6

k_path = kappa_model(d_um_path)

# Stop once kappa drops below threshold
valid = k_path > kappa_threshold

s_valid = s[valid]
k_valid = k_path[valid]
d_valid = d_um_path[valid]

# =====================
# PHASE CORRECTION
# =====================

theta_tail = np.trapz(k_valid, s_valid)

print(f"Theta_tail = {theta_tail:.4f} rad")
print(f"Theta_tail/pi = {theta_tail/np.pi:.4f}")
print(f"Max displacement used = {d_valid[-1]:.3f} um")
print(f"Arc length used = {s_valid[-1]*1e6:.3f} um")