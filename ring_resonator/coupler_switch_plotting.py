import pandas as pd

# =====================
# LOAD CSV
# =====================
df = pd.read_csv("ring_resonator/coupler_switch_pcm(singlewg)_sweep.csv")

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
    "P_off",      # OFF / cross
    "P_on"        # ON / through
]

# =====================
# PRINT
# =====================
print("\n========== TOP DESIGNS ==========\n")
print(top[cols].to_string(index=False))