import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Import the data from the CSV files
df_COMSOL_HfO2_ALDshield_reducedAu = pd.read_csv("modulator_data/COMSOL_HfO2_ALDshield_reducedAu.csv")
df_Lum_HfO2_ALDshield_reducedAu = pd.read_csv("modulator_data/Lum_HfO2_ALDshield_reducedAu.csv")

# Convert gap from meters to nanometers for better readability (Lum HfO2 already in nm)
df_COMSOL_HfO2_ALDshield_reducedAu['Gap'] = df_COMSOL_HfO2_ALDshield_reducedAu['Gap'] * 1e9
# ---------- Lum HfO2 data is already in nm ----------------------

# Print out list of Eavg values and gap from COMSOL data
print("\nCOMSOL HfO2 ALD Shield Reduced Au Eavg values (V/um) and Gap (nm):")
for index, row in df_COMSOL_HfO2_ALDshield_reducedAu.iterrows():
    print(f"Gap: {row['Gap']} nm, Eavg: {row['Eavg']} V/um")

# Plot Eavg vs Gap for COMSOL ALDshield reduced Au
plt.figure(figsize=(10, 6))
plt.plot(df_COMSOL_HfO2_ALDshield_reducedAu['Gap'], df_COMSOL_HfO2_ALDshield_reducedAu['Eavg'], marker='o', label='COMSOL HfO2 ALDshield Reduced Au', color='orange')
plt.title('Average Electric Field (Eavg) vs Gap for COMSOL HfO2 ALDshield Reduced Au')
plt.xlabel('Gap (nm)')
plt.ylabel('Average Electric Field (Eavg) (V/um)')
plt.grid(True)
plt.legend()
plt.show()