import numpy as np

eps0 = 8.854e-12

electrode_spacing = 1.5e-6
g = 500e-9
H = 0.350e-6
t_shield_core = 0.5 * g

h_eff = H + t_shield_core
eps_eff = 12.0   # rough guess

C_prime = eps0 * eps_eff * h_eff / electrode_spacing

print("C' ≈", C_prime, "F/m")
print("C' ≈", C_prime * 1e12 / 1e6, "fF/um")

R = 30e-6
L_cpl = 3e-6
L_ring = 2*np.pi*R + 2*L_cpl
L_active = L_ring - L_cpl

C_total = C_prime * L_active
print("C_total ≈", C_total, "F")
print("C_total ≈", C_total * 1e15, "fF")

# ============================================================
# METAL / ELECTRICAL PARAMETERS
# ============================================================
sigma_au = 4.1e7          # S/m, gold conductivity
rho_au = 1 / sigma_au     # ohm*m

metal_w = 1.0e-6          # m
metal_t = 100e-9          # m

A_metal = metal_w * metal_t   # cross-sectional area of one electrode

# resistance per unit length
R_prime = rho_au / A_metal    # ohm/m

# ============================================================
# DISTRIBUTED RC BANDWIDTH (L^2 scaling)
# ============================================================
f_RC_dist = 1 / (2 * np.pi * R_prime * C_prime * L_active**2)

# ============================================================
# ALSO COMPUTE LUMPED VERSION FOR REFERENCE
# ============================================================
R_total_metal = R_prime * L_active
C_total = C_prime * L_active

R_driver = 50
f_RC_lumped_with_driver = 1 / (2 * np.pi * (R_total_metal + R_driver) * C_total)

# ============================================================
# PRINT
# ============================================================
print("========== RC ESTIMATE ==========")
print(f"L_active               = {L_active*1e6:.3f} um")
print(f"Metal area             = {A_metal:.3e} m^2")
print(f"R' (metal)             = {R_prime:.3e} ohm/m")
print(f"C'                     = {C_prime:.3e} F/m")
print(f"C'                     = {C_prime*1e6*1e15:.3f} fF/um")
print(f"Metal R over L_active  = {R_total_metal:.3f} ohm")
print(f"Total C over L_active  = {C_total*1e15:.3f} fF")
print(f"f_RC distributed       = {f_RC_dist/1e9:.3f} GHz")
print(f"f_RC lumped            = {f_RC_lumped_with_driver/1e9:.3f} GHz")