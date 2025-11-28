import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Import the data from the CSV files

df_HfO2_ALD_shield = pd.read_csv("modulator_results_analysis/modulator_sweep_data/HfO2_ALDshield.csv")
df_HfO2_NonALD_shield = pd.read_csv("modulator_results_analysis/modulator_sweep_data/HfO2_NonALDshield.csv")
df_SiO2_shield = pd.read_csv("modulator_results_analysis/modulator_sweep_data/SiO2_shield.csv")
df_Lum_HfO2_ALDetched = pd.read_csv("modulator_results_analysis/modulator_sweep_data/Lum_HfO2_ALDetched.csv")


# Convert gap from meters to nanometers for better readability (Lum HfO2 already in nm)
df_HfO2_ALD_shield['Gap'] = df_HfO2_ALD_shield['Gap'] * 1e9
df_HfO2_NonALD_shield['Gap'] = df_HfO2_NonALD_shield['Gap'] * 1e9
df_SiO2_shield['Gap'] = df_SiO2_shield['Gap'] * 1e9

# Print list of loss values and gap for each configuration
print("HfO2 ALD Shield Loss values (dB/cm) and Gap (nm):")
for index, row in df_HfO2_ALD_shield.iterrows():
    print(f"Gap: {row['Gap']:.1f} nm, Loss: {row['Loss']:.4f} dB/cm")
print("\nHfO2 Non-ALD Shield Loss values (dB/cm) and Gap (nm):")
for index, row in df_HfO2_NonALD_shield.iterrows():
    print(f"Gap: {row['Gap']:.1f} nm, Loss: {row['Loss']:.4f} dB/cm")
print("\nSiO2 Shield Loss values (dB/cm) and Gap (nm):")
for index, row in df_SiO2_shield.iterrows():
    print(f"Gap: {row['Gap']:.1f} nm, Loss: {row['Loss']:.4f} dB/cm")
print("\nLumeical HfO2 ALD Shield with Top Layer Etched Loss values (dB/cm) and Gap (nm):")
for index, row in df_Lum_HfO2_ALDetched.iterrows():
    print(f"Gap: {row['gap']:.1f} nm, Loss (TE): {row['loss(TE)']:.4f} dB/cm, Loss (TM): {row['loss(TM)']:.4f} dB/cm")

# Plot VpiL vs gap for each configuration on the same graph (colored lines with markers)
plt.figure(figsize=(8, 6))
#plt.plot(df_HfO2_ALD_shield['Gap'], df_HfO2_ALD_shield['VpiL'], marker='o', label='HfO2 ALD Shield', color='blue')
plt.plot(df_HfO2_NonALD_shield['Gap'], df_HfO2_NonALD_shield['VpiL'], marker='s', label='HfO2 Non-ALD Shield', color='green')
#plt.plot(df_SiO2_shield['Gap'], df_SiO2_shield['VpiL'], marker='^', label='SiO2 Shield', color='red')
plt.xlabel('Gap (nm)')
plt.ylabel('VpiL (V*cm)')
plt.title('VpiL vs Gap')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Plot Loss vs gap for each configuration on the same graph
plt.figure(figsize=(8, 6))
plt.plot(df_HfO2_ALD_shield['Gap'], df_HfO2_ALD_shield['Loss'], marker='o', label='HfO2 ALD Shield', color='blue')
plt.plot(df_HfO2_NonALD_shield['Gap'], df_HfO2_NonALD_shield['Loss'], marker='s', label='HfO2 Non-ALD Shield', color='green')
plt.plot(df_SiO2_shield['Gap'], df_SiO2_shield['Loss'], marker='^', label='SiO2 Shield', color='red')
plt.xlabel('Gap (nm)')
plt.ylabel('Loss (dB/cm)')
plt.title('Loss vs Gap')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Plot loss vs gap for just the HfO2 non-ALD shield configuration and the Lum HfO2 ALD shield with top layer etched data
plt.figure(figsize=(8, 6))
plt.plot(df_HfO2_NonALD_shield['Gap'], df_HfO2_NonALD_shield['Loss'], marker='s', label='COMSOL (TE)', color='green')
plt.plot(df_Lum_HfO2_ALDetched['gap'], df_Lum_HfO2_ALDetched['loss(TE)'], marker='o', label='Lumeical (TE)', color='blue')
plt.plot(df_Lum_HfO2_ALDetched['gap'], df_Lum_HfO2_ALDetched['loss(TM)'], marker='^', label='Lumeical (TM)', color='red')
plt.xlabel('Gap (nm)')
plt.ylabel('Loss (dB/cm)')
plt.title('Loss vs Gap (COMSOL vs Lumeical)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Calculate and plot figure of merit (VpiL * Loss) vs gap for each configuration
plt.figure(figsize=(8, 6))
plt.plot(df_HfO2_ALD_shield['Gap'], df_HfO2_ALD_shield['VpiL'] * df_HfO2_ALD_shield['Loss'], marker='o', label='HfO2 ALD Shield', color='blue')
plt.plot(df_HfO2_NonALD_shield['Gap'], df_HfO2_NonALD_shield['VpiL'] * df_HfO2_NonALD_shield['Loss'], marker='s', label='HfO2 Non-ALD Shield', color='green')
plt.plot(df_SiO2_shield['Gap'], df_SiO2_shield['VpiL'] * df_SiO2_shield['Loss'], marker='^', label='SiO2 Shield', color='red')
plt.xlabel('Gap (nm)')
plt.ylabel('VpiL * Loss (V*db)')
plt.title('VpiL*Loss vs Gap')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Plot electric field energy density vs gap for each configuration
plt.figure(figsize=(8, 6))
plt.plot(df_HfO2_ALD_shield['Gap'], df_HfO2_ALD_shield['E2dens'], marker='o', label='HfO2 ALD Shield', color='blue')
plt.plot(df_HfO2_NonALD_shield['Gap'], df_HfO2_NonALD_shield['E2dens'], marker='s', label='HfO2 Non-ALD Shield', color='green')
plt.plot(df_SiO2_shield['Gap'], df_SiO2_shield['E2dens'], marker='^', label='SiO2 Shield', color='red')
plt.xlabel('Gap (nm)')
plt.ylabel('Electric Field Energy Density (J/m^2)')
plt.title('Electric Field Energy Density vs Gap')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()