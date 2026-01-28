import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Import the data from the CSV files
df_COMSOL_HfO2_ALDshield_reducedAu = pd.read_csv("modulator_data/COMSOL_HfO2_ALDshield_reducedAu.csv")
df_Lum_HfO2_ALDshield_reducedAu = pd.read_csv("modulator_data/Lum_HfO2_ALDshield_reducedAu.csv")

# Convert gap from meters to nanometers for better readability (Lum HfO2 already in nm)
df_COMSOL_HfO2_ALDshield_reducedAu['Gap'] = df_COMSOL_HfO2_ALDshield_reducedAu['Gap'] * 1e9
# ---------- Lum HfO2 data is already in nm ----------------------


# Print list of TE loss values and gap from Lumerical data
print("\nLumerical HfO2 ALD Shield Reduced Au TE Loss values (dB/cm) and Gap (nm):")
for index, row in df_Lum_HfO2_ALDshield_reducedAu.iterrows():
    print(f"Gap: {row['gap']:.1f} nm, TE Loss: {row['loss(TE)']:.4f} dB/cm")


# Plot the TE Loss vs gap for the Lumerical HfO2 ALD shield data and the Lumerical HfO2 reduced Au data
plt.figure(figsize=(10, 6))
plt.plot(df_Lum_HfO2_ALDshield_reducedAu['gap'], df_Lum_HfO2_ALDshield_reducedAu['loss(TE)'], marker='s', label='Lumerical HfO2 Reduced Au', color='orange')
plt.xlabel('Gap (nm)')
plt.ylabel('TE Loss (dB/cm)')
plt.title('TE Loss vs Gap for Lumerical HfO2 ALD Shield and Reduced Au Data')
plt.legend()
plt.grid(True)
plt.show()

