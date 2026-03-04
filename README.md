# SRN Electro-Optic Modulator Inverse Design Framework

Author: Nakul  
Institution: UC San Diego  
Project: Silicon-Rich Nitride (SRN) Electro-Optic Modulator Optimization  

---

# 1. Overview

This repository implements a physics-driven inverse design loop for a silicon-rich nitride (SRN) electro-optic modulator cross-section.

The workflow couples:

- Lumerical DEVICE (electrostatics)
- Lumerical MODE (optical eigenmode solver)
- Python-based overlap integrals
- Finite-difference gradient optimization

The goal is to minimize:

$$
J = w_1 \frac{V_{\pi}L}{(V_{\pi}L)_0}
  + w_2 \frac{\text{loss}}{(\text{loss})_0}
$$

over geometric parameters.

This is a full end-to-end simulation-driven optimization framework.

---

# 2. Physics Model

The modulator operates via EFISH (Electric Field Induced Second Harmonic).

We assume:

- Third-order nonlinearity χ³ in SRN
- Effective χ² induced by DC field:
  
  $$
  \chi^{(2)}_{\text{eff}} = \frac{3}{2} \chi^{(3)} E_{\text{DC}}
  $$

- Small-signal AC modulation (linear regime)
- No carrier injection
- No plasma dispersion
- No thermal effects
- 2D cross-sectional approximation

Effective index perturbation:

$$
\Delta n_{\text{eff}} =
\frac{\int \Delta \varepsilon |E|^2 dA}
{2 \int \varepsilon |E|^2 dA}
$$

Modulation efficiency:

$$
V_{\pi}L = \frac{\lambda}{2 \Delta n_{\text{eff}}}
$$

Loss is extracted directly from the MODE solver.

---

# 3. Optimization Variables

Optimized geometry parameters:

- g — electrode-core gap
- t_shield_gapL
- t_shield_gapR
- t_shield_core

Clamped for physical feasibility:

- g ∈ [150 nm, 3 µm]
- shield thicknesses ∈ [10 nm, 0.9g]

---

# 4. Data Flow

1. Parameters pushed to Lumerical
2. Electrostatics solved → E_DC and E_AC fields
3. Optical mode solved → |E|² and loss
4. Electrostatics interpolated onto optical grid
5. Overlap integrals computed
6. Objective evaluated
7. Finite-difference gradients computed
8. Parameters updated

---

# 5. Numerical Methods

## Optimization Method (Finite-Difference + Gradient Descent)

### Finite-Difference Gradient

For each design parameter \(p\), we estimate the objective sensitivity using a **central finite difference**:


$$\frac{dJ}{dp} \approx \frac{J(p+h) - J(p-h)}{2h}$$


with perturbation size

$$
h = \max(\text{rel}\cdot |p|,\ \text{abs\_min})
$$

where:
- `rel` is a relative perturbation fraction (e.g., 0.03 for 3%)
- `abs_min` is a minimum absolute perturbation in meters (prevents tiny steps)

---

### Update Rule (Magnitude-Based Gradient Descent)

We perform a **magnitude-based** gradient descent update (not sign descent):

$$
p_{\text{new}} = p - \alpha \, s_p \, \frac{dJ}{dp}
$$

where:
- \($\alpha$\) is the step size (`alpha` / `step_frac` depending on implementation)
- \($s_p$\) is a characteristic scale used to keep steps reasonable and unit-consistent  
  (for geometry parameters, this is typically \(s_p = |p|\) so that steps are relative)

This uses the **actual gradient magnitude**, so parameters with larger sensitivity receive larger updates, while still keeping the update roughly *relative to the parameter scale*.

---

# 6. Current Status

✔ End-to-end inverse design loop functional  
✔ Electrostatics + optical coupling validated  
✔ Multi-parameter optimization demonstrated  
✔ Loss-weighted objective supported  

Future improvements:
- Adjoint gradient method
- Line search or trust region
- Hessian-based update
- RF modeling

---

# 7. Requirements

- Ansys Lumerical DEVICE + MODE
- Python 3.9+
- numpy
- pandas
- scipy
- h5py

---
