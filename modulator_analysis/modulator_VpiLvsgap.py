import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Import the data from the CSV files
df_COMSOL_HfO2_ALDshield = pd.read_csv("modulator_data/COMSOL_HfO2_ALDshield.csv")
df_COMSOL_HfO2_ALDshield_etched = pd.read_csv("modulator_data/COMSOL_HfO2_ALDshield_etched.csv")
df_COMSOL_SiO2_ALDshield = pd.read_csv("modulator_data/COMSOL_SiO2_ALDshield.csv")
df_COMSOL_HfO2_ALDshield_reducedAu = pd.read_csv("modulator_data/COMSOL_HfO2_ALDshield_reducedAu.csv")
df_Lum_HfO2_ALDshield_etched = pd.read_csv("modulator_data/Lum_HfO2_ALDshield_etched.csv")
df_Lum_HfO2_ALDshield_etched_fine = pd.read_csv("modulator_data/Lum_HfO2_ALDshield_etched_fine.csv")
df_Lum_HfO2_BOX_ALDshield_etched = pd.read_csv("modulator_data/Lum_HfO2_BOX_ALDshield_etched.csv")
df_Lum_HfO2_ALDshield = pd.read_csv("modulator_data/Lum_HfO2_ALDshield.csv")
df_Lum_HfO2_ALDshield_reducedAu = pd.read_csv("modulator_data/Lum_HfO2_ALDshield_reducedAu.csv")

# Convert gap from meters to nanometers for better readability (Lum HfO2 already in nm)
df_COMSOL_HfO2_ALDshield['Gap'] = df_COMSOL_HfO2_ALDshield['Gap'] * 1e9
df_COMSOL_HfO2_ALDshield_etched['Gap'] = df_COMSOL_HfO2_ALDshield_etched['Gap'] * 1e9
df_COMSOL_SiO2_ALDshield['Gap'] = df_COMSOL_SiO2_ALDshield['Gap'] * 1e9
df_COMSOL_HfO2_ALDshield_reducedAu['Gap'] = df_COMSOL_HfO2_ALDshield_reducedAu['Gap'] * 1e9
# ---------- Lum HfO2 data is already in nm ----------------------


# Print VpiL values and gap
print("\nHfO2 ALD Shield VpiL values (V·cm) and Gap (nm):")
for index, row in df_COMSOL_HfO2_ALDshield.iterrows():
    print(f"Gap: {row['Gap']:.1f} nm, VpiL: {row['VpiL']:.4f} V·cm")
print("\nHfO2 Reduced Au VpiL values (V·cm) and Gap (nm):")
for index, row in df_COMSOL_HfO2_ALDshield_reducedAu.iterrows():
    print(f"Gap: {row['Gap']:.1f} nm, VpiL: {row['VpiL']:.4f} V·cm")
    

# Plot the VpiL vs gap for the COMSOL HfO2 ALD shield data and the COMSOL HfO2 reduced Au data
plt.figure(figsize=(10, 6))
plt.plot(df_COMSOL_HfO2_ALDshield['Gap'], df_COMSOL_HfO2_ALDshield['VpiL'], marker='o', label='COMSOL HfO2 ALD Shield', color='blue')
plt.plot(df_COMSOL_HfO2_ALDshield_reducedAu['Gap'], df_COMSOL_HfO2_ALDshield_reducedAu['VpiL'], marker='s', label='COMSOL HfO2 Reduced Au', color='orange')
plt.xlabel('Gap (nm)')
plt.ylabel('VπL (V·cm)')
plt.title('VπL vs Gap for COMSOL HfO2 ALD Shield and Reduced Au Data')
plt.legend()
plt.grid(True)
plt.show()