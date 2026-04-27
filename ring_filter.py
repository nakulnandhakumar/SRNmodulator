import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV file
df = pd.read_csv("ring_resonator/n_k_sbs.csv")

# Plot n and k vs wavelength
plt.figure(figsize=(12, 5))
plt.plot(df["wavelength"] * 1e9, df["n_amorphous"], label="n (amorphous)")
plt.plot(df["wavelength"] * 1e9, df["n_crystalline"], label="n (crystalline)")
plt.plot(df["wavelength"] * 1e9, df["k_amorphous"], label="k (amorphous)")
plt.plot(df["wavelength"] * 1e9, df["k_crystalline"], label="k (crystalline)")
plt.xlabel("Wavelength (nm)")
plt.ylabel("Refractive Index (n) / Extinction Coefficient (k)")
plt.title("Refractive Index and Extinction Coefficient vs Wavelength")
plt.legend()
plt.grid()
plt.show()