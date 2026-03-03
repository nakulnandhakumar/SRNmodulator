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
        rel=0.02,         # relative FD step (2%)
        abs_min=5e-9,   # minimum absolute FD step (5 nm)
        alpha_init=0.05,     # initial step scale
        beta=0.5,            # shrink factor
        min_alpha=1e-3,
    ):
        self.session = session
        self.refs = refs
        self.opt_keys = opt_keys
        self.weights = weights if weights is not None else {}
        self.rel = rel                # relative FD step (for gradient)
        self.abs_min = abs_min        # minimum FD step (meters)
        self.alpha_init = alpha_init
        self.beta = beta
        self.min_alpha = min_alpha

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
    # Backtracking line search update
    # -------------------------------------------------
    def line_search_update(self, params, grads):

        # Current objective
        results_current = evaluate_params(self.session, params)
        J_current = objective_function(results_current, self.refs, self.weights)

        alpha = self.alpha_init
        
        norm = np.sqrt(sum((grads[k] * abs(params[k]))**2 for k in self.opt_keys))

        if norm < 1e-16:
            print("[LS] Gradient norm ~0. No update.")
            return params

        while alpha > self.min_alpha:

            trial_params = params.copy()

            for key in self.opt_keys:

                # scaled gradient
                g_scaled = grads[key] * abs(params[key])

                # normalized direction
                direction = g_scaled / norm

                trial_params[key] -= alpha * direction

            # Evaluate trial
            results_trial = evaluate_params(self.session, trial_params)
            J_trial = objective_function(results_trial, self.refs, self.weights)

            print(f"[LS] alpha={alpha:.4f}, J_trial={J_trial:.6f}")

            if J_trial < J_current:
                print("[LS] Accepted step.")
                return trial_params

            alpha *= self.beta  # shrink step

        print("[LS] Step rejected — returning original params.")
        return params

    # -------------------------------------------------
    # Single optimization step
    # -------------------------------------------------
    def step(self, params):
        grads = self.compute_gradient(params)
        new_params = self.line_search_update(params, grads)
        return new_params, grads