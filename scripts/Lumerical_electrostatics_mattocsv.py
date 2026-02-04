import h5py
import numpy as np

with h5py.File("./modulator_data/Lumerical_electrostatics/mat/SRN_modulator_electrostatics.mat", "r") as f:
    print("Keys:", list(f.keys()))

    E = np.array(f["E"])
    verts = np.array(f["vertices"])

Ex = E[0, :]
Ey = E[1, :]
Ez = E[2, :]

x = verts[0, :]
y = verts[1, :]
z = verts[2, :]

print(np.max(np.sqrt(Ex**2 + Ey**2)))
print(np.max(y))