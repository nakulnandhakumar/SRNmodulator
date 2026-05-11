import pandas as pd

# =====================
# LOAD CSV
# =====================
df = pd.read_csv("ring_resonator/coupler_switch_pcm_sweep.csv")

# =====================
# SORT BY ER (best first)
# =====================
top_n = 5

top = df.sort_values(by="ER_dB", ascending=False).head(top_n)

# =====================
# SELECT ONLY RELEVANT COLUMNS
# =====================
cols = [
    "g_nm",
    "t_gap_pcm_nm",
    "t_pcm_nm",
    "P_sym",           # Symmetric / cross
    "P_antisym",        # Antisymmetric / through
    "L_design_um",
    "Omega_sym",
    "Omega_antisym",
    "loss_eff_antisym",
    "loss_eff_sym",
]

# =====================
# PRINT
# =====================
print("\n========== TOP DESIGNS ==========\n")
print(top[cols].to_string(index=False))