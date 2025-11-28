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


# Print list of loss values and gap for each configuration
print("HfO2 ALD Shield Loss values (dB/cm) and Gap (nm):")
for index, row in df_COMSOL_HfO2_ALDshield.iterrows():
    print(f"Gap: {row['Gap']:.1f} nm, Loss: {row['Loss']:.4f} dB/cm")
print("\nHfO2 Non-ALD Shield Loss values (dB/cm) and Gap (nm):")
for index, row in df_COMSOL_HfO2_ALDshield_etched.iterrows():
    print(f"Gap: {row['Gap']:.1f} nm, Loss: {row['Loss']:.4f} dB/cm")
print("\nSiO2 Shield Loss values (dB/cm) and Gap (nm):")
for index, row in df_COMSOL_SiO2_ALDshield.iterrows():
    print(f"Gap: {row['Gap']:.1f} nm, Loss: {row['Loss']:.4f} dB/cm")
print("\nLumeical HfO2 ALD Shield with Top Layer Etched Loss values (dB/cm) and Gap (nm):")
for index, row in df_Lum_HfO2_ALDshield_etched.iterrows():
    print(f"Gap: {row['gap']:.1f} nm, Loss (TE): {row['loss(TE)']:.4f} dB/cm, Loss (TM): {row['loss(TM)']:.4f} dB/cm")
    

# Plot Loss vs gap for each configuration on the same graph
plt.figure(figsize=(8, 6))
plt.plot(df_COMSOL_HfO2_ALDshield['Gap'], df_COMSOL_HfO2_ALDshield['Loss'], marker='o', label='HfO2 ALD Shield', color='blue')
plt.plot(df_COMSOL_HfO2_ALDshield_etched['Gap'], df_COMSOL_HfO2_ALDshield_etched['Loss'], marker='s', label='HfO2 Non-ALD Shield', color='green')
plt.plot(df_COMSOL_SiO2_ALDshield['Gap'], df_COMSOL_SiO2_ALDshield['Loss'], marker='^', label='SiO2 Shield', color='red')
plt.xlabel('Gap (nm)')
plt.ylabel('Loss (dB/cm)')
plt.title('Loss vs Gap')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


# Plot loss vs gap for just the HfO2 non-ALD shield configuration and the Lum HfO2 ALD shield with top layer etched data
plt.figure(figsize=(8, 6))
plt.plot(df_COMSOL_HfO2_ALDshield_etched['Gap'], df_COMSOL_HfO2_ALDshield_etched['Loss'], marker='s', label='COMSOL (TE)', color='green')
plt.plot(df_Lum_HfO2_ALDshield_etched['gap'], df_Lum_HfO2_ALDshield_etched['loss(TE)'], marker='o', label='Lumeical (TE)', color='blue')
plt.plot(df_Lum_HfO2_ALDshield_etched['gap'], df_Lum_HfO2_ALDshield_etched['loss(TM)'], marker='^', label='Lumeical (TM)', color='red')
plt.xlabel('Gap (nm)')
plt.ylabel('Loss (dB/cm)')
plt.title('Loss vs Gap (COMSOL vs Lumeical)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()