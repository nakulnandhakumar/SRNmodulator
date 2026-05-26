import pandas as pd
import os

# =====================
# LOAD CSV
# =====================

# Directory structure
coupling_direction = "vertical"  # "lateral" or "vertical"
pcm_loading_direction = "top_pcm" # "side_pcm" or "top_pcm"

design_dir = (
    f"./coupler_switch/coupler_switch_design_sweep_results/"
    f"{coupling_direction}_coupling/"
    f"{pcm_loading_direction}"
)

# Filename parameters
W_bus_nm = 350
H_bus_nm = 450

W_coupler_nm = 350
H_coupler_nm = 450

g_min_nm = 200
g_max_nm = 300

t_pcm_min_nm = 10
t_pcm_max_nm = 40

t_gap_min_nm = 0
t_gap_max_nm = 20

polarization = "TM" # "TE" or "TM"

filename = (
    f"design_"
    f"{polarization}_"
    f"Wbus{W_bus_nm}nm_"
    f"Hbus{H_bus_nm}nm_"
    f"Wcpl{W_coupler_nm}nm_"
    f"Hcpl{H_coupler_nm}nm_"
    f"g{g_min_nm}-{g_max_nm}nm_"
    f"tpcm{t_pcm_min_nm}-{t_pcm_max_nm}nm_"
    f"tgap{t_gap_min_nm}-{t_gap_max_nm}nm.csv"
)

csv_path = os.path.join(design_dir, filename)

df = pd.read_csv(csv_path)

# =====================
# FILTER DESIGNS
# Keep only ER >= 20 dB
# =====================
#filtered = df[df["ER_dB"] >= 20]

# =====================
# SORT BY COUPLING LENGTH
# Smallest coupling length first
# =====================
filtered = df.sort_values(by="ER_dB", ascending=False)

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
    "L_corrected_design_um",
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