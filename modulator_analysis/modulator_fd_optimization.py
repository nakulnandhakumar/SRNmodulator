"""
modulator_fd_optimization.py
----------------------------

Finite-difference gradient-based optimizer.

Method:
- Central finite differences for each parameter
- Scalar objective J
- Sign-based descent update:
      p_new = p - α |p| sign(dJ/dp)

Key design decisions:
- Relative perturbation size (rel)
- Minimum absolute perturbation (abs_min)
- Fixed update fraction (step_frac)
- No line search
- No convergence check
- No second-order information

This is intentionally simple:
- Easy to debug
- Clear sensitivity inspection
- Computationally expensive (2 solves per parameter)

Suitable for:
- Small parameter sets (≤5 variables)
- Demonstration of inverse design loop
"""

import copy
import numpy as np
from modulator_analysis.modulator_evaluate import evaluate_params
from modulator_analysis.modulator_objective import objective_function


class FDOptimizer:
    """
    Finite-difference gradient-based optimizer for SRN modulator geometry.
    """

    def __init__(
        self,
        session,
        refs,
        opt_keys,
        weights=None,
        rel=0.03,
        step_frac=0.05,
        abs_min=10e-9,
    ):
        self.session = session
        self.refs = refs
        self.opt_keys = opt_keys
        self.weights = weights if weights is not None else {}
        self.rel = rel                # relative FD step (for gradient)
        self.step_frac = step_frac    # relative update step
        self.abs_min = abs_min        # minimum FD step (meters)

    # -------------------------------------------------
    # Finite difference step size
    # -------------------------------------------------
    def fd_step(self, p):
        return max(abs(p) * self.rel, self.abs_min)

    # -------------------------------------------------
    # Compute central FD gradient
    # -------------------------------------------------
    # Central finite difference:
    #   grad ≈ (J(p+h) - J(p-h)) / (2h)
    #
    # Requires two full simulation pipelines per parameter.
    def compute_gradient(self, params):
        grads = {}

        for key in self.opt_keys:

            p0 = params[key]
            h = self.fd_step(p0)

            p_plus  = copy.deepcopy(params)
            p_minus = copy.deepcopy(params)

            p_plus[key]  = p0 + h
            p_minus[key] = p0 - h

            # Evaluate objective at p+h
            results_plus = evaluate_params(self.session, p_plus)
            Jp = objective_function(results_plus, self.refs, self.weights)

            # Evaluate objective at p-h
            results_minus = evaluate_params(self.session, p_minus)
            Jm = objective_function(results_minus, self.refs, self.weights)

            grad = (Jp - Jm) / (2 * h)
            grads[key] = grad

            print(
                f"[FD] {key}: "
                f"h = {h*1e9:.1f} nm, "
                f"grad = {grad:.3e}"
            )

        return grads

    # -------------------------------------------------
    # Gradient descent update
    # -------------------------------------------------
    # Sign-based descent:
    # Step magnitude proportional to parameter size.
    # This avoids large jumps when parameters vary in scale.
    def update(self, params, grads):
        new_params = params.copy()

        for key, grad in grads.items():
            if grad == 0:
                continue

            delta = self.step_frac * abs(params[key]) * np.sign(grad)
            new_params[key] -= delta

            print(f"[UPDATE] {key}: Δ = {-delta*1e9:.2f} nm")

        return new_params

    # -------------------------------------------------
    # Single optimization step
    # -------------------------------------------------
    def step(self, params):
        grads = self.compute_gradient(params)
        new_params = self.update(params, grads)
        return new_params, grads