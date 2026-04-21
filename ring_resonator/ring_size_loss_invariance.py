import numpy as np

# ============================================================
# RACETRACK GEOMETRY
# ============================================================
R_old = 20e-6
L_cpl = 3e-6
L_straight_total = 2 * L_cpl

L_ring_old = 2 * np.pi * R_old + L_straight_total
L_active_old = L_ring_old - L_cpl
L_passive = L_cpl

# ============================================================
# LOSS VALUES AND MODEL
# ============================================================
def dBcm_to_nepers_per_m(alpha_dB_cm):
    return alpha_dB_cm * 100 / (10 * np.log10(np.e))

def nepers_per_m_to_dBcm(alpha_np):
    return alpha_np * (10 * np.log10(np.e)) / 100

alpha_roughness_dB_cm = 3
extra_loss_dB_cm_old = 18.01

# baseline (no extra loss)
alpha_active_base_dB_cm = 0.39982 + alpha_roughness_dB_cm
alpha_passive_base_dB_cm = 0 + alpha_roughness_dB_cm

# total old loss
alpha_active_dB_cm_old = 0.39982 + alpha_roughness_dB_cm + extra_loss_dB_cm_old
alpha_passive_dB_cm_old = 0 + alpha_roughness_dB_cm + extra_loss_dB_cm_old

# convert to nepers/m
alpha_active_old = dBcm_to_nepers_per_m(alpha_active_dB_cm_old)
alpha_passive_old = dBcm_to_nepers_per_m(alpha_passive_dB_cm_old)

alpha_active_base = dBcm_to_nepers_per_m(alpha_active_base_dB_cm)
alpha_passive_base = dBcm_to_nepers_per_m(alpha_passive_base_dB_cm)

# invariance condition: total loss around ring must be same for old and new geometries
S_old = alpha_active_old * L_active_old + alpha_passive_old * L_passive

# ============================================================
# NEW RING GEOMETRY
# ============================================================
R_new_list = [30e-6, 40e-6, 50e-6, 60e-6]

for R_new in R_new_list:
    # new geometry
    L_ring_new = 2 * np.pi * R_new + L_straight_total
    L_active_new = L_ring_new - L_cpl

    # Solve exactly for alpha_extra_new:
    #
    # (alpha_active_base + alpha_extra_new) * L_active_new
    # + (alpha_passive_base + alpha_extra_new) * L_passive
    # = S_old
    #
    # => alpha_extra_new * (L_active_new + L_passive)
    #    = S_old - alpha_active_base*L_active_new - alpha_passive_base*L_passive
    #
    alpha_extra_new = (
        S_old
        - alpha_active_base * L_active_new
        - alpha_passive_base * L_passive
    ) / (L_active_new + L_passive)

    extra_loss_dB_cm_new = nepers_per_m_to_dBcm(alpha_extra_new)

    # total new losses for reference
    alpha_active_new = alpha_active_base + alpha_extra_new
    alpha_passive_new = alpha_passive_base + alpha_extra_new

    # check exact invariance
    S_new = alpha_active_new * L_active_new + alpha_passive_new * L_passive

    print(f"R_new = {R_new*1e6:.1f} um")
    print(f"  L_ring_new              = {L_ring_new*1e6:.4f} um")
    print(f"  L_active_new            = {L_active_new*1e6:.4f} um")
    print(f"  required extra loss     = {extra_loss_dB_cm_new:.6f} dB/cm")
    print(f"  total active loss       = {nepers_per_m_to_dBcm(alpha_active_new):.6f} dB/cm")
    print(f"  total passive loss      = {nepers_per_m_to_dBcm(alpha_passive_new):.6f} dB/cm")
    print(f"  invariance check error  = {abs(S_new - S_old):.3e}\n")