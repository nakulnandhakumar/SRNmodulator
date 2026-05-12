import pandas as pd

# Load Excel file
df = pd.read_excel("coupler_switch/n_k_sbs.xlsx")

# Rename columns for clarity
df.columns = [
    "wavelength",
    "n_amorphous",
    "n_crystalline",
    "k_amorphous",
    "k_crystalline"
]

# Save to CSV
df.to_csv("coupler_switch/n_k_sbs.csv", index=False)