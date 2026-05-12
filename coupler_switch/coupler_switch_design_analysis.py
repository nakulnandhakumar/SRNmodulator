import pandas as pd

# =====================
# LOAD CSV
# =====================
df = pd.read_csv("ring_resonator/coupler_switch_side_pcm_sweep.csv")

# =====================
# FILTER DESIGNS
# Keep only ER >= 20 dB
# =====================
filtered = df[df["ER_dB"] >= 20]

# =====================
# SORT BY COUPLING LENGTH
# Smallest coupling length first
# =====================
filtered = filtered.sort_values(by="L_design_um", ascending=True)

# =====================
# SELECT TOP N
# =====================
top_n = 20
top = filtered.head(top_n)

# =====================
# SELECT RELEVANT COLUMNS
# =====================
cols = [
    "g_nm",
    "t_pcm_nm",
    "t_gap_pcm_nm",
    "P_sym",
    "P_antisym",
    "L_design_um",
    "Omega_sym",
    "Omega_antisym",
    "loss_eff_antisym",
    "ER_dB",
]

# =====================
# PRINT
# =====================
print("\n========== TOP DESIGNS ==========\n")

print(top[cols].to_string(index=False))