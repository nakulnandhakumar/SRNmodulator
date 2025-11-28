import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Import the data from the CSV files
df_COMSOL_HfO2_ALDshield = pd.read_csv("modulator_data/COMSOL_HfO2_ALDshield.csv")
df_COMSOL_HfO2_ALDshield_etched = pd.read_csv("modulator_data/COMSOL_HfO2_ALDshield_etched.csv")
df_COMSOL_SiO2_ALDshield = pd.read_csv("modulator_data/COMSOL_SiO2_ALDshield.csv")
df_Lum_HfO2_ALDshield_etched = pd.read_csv("modulator_data/Lum_HfO2_ALDshield_etched.csv")

# Convert gap from meters to nanometers for better readability (Lum HfO2 already in nm)
df_COMSOL_HfO2_ALDshield['Gap'] = df_COMSOL_HfO2_ALDshield['Gap'] * 1e9
df_COMSOL_HfO2_ALDshield_etched['Gap'] = df_COMSOL_HfO2_ALDshield_etched['Gap'] * 1e9
df_COMSOL_SiO2_ALDshield['Gap'] = df_COMSOL_SiO2_ALDshield['Gap'] * 1e9
# ---------- Lum HfO2 data is already in nm ----------------------

# Plot electric field energy density vs gap for each configuration
plt.figure(figsize=(8, 6))
plt.plot(df_COMSOL_HfO2_ALDshield['Gap'], df_COMSOL_HfO2_ALDshield['E2dens'], marker='o', label='HfO2 ALD Shield', color='blue')
plt.plot(df_COMSOL_HfO2_ALDshield_etched['Gap'], df_COMSOL_HfO2_ALDshield_etched['E2dens'], marker='s', label='HfO2 Non-ALD Shield', color='green')
plt.plot(df_COMSOL_SiO2_ALDshield['Gap'], df_COMSOL_SiO2_ALDshield['E2dens'], marker='^', label='SiO2 Shield', color='red')
plt.xlabel('Gap (nm)')
plt.ylabel('Electric Field Energy Density (J/m^2)')
plt.title('Electric Field Energy Density vs Gap')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()