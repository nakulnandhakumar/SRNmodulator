# modulator_analysis/fd_optimization.py
import copy
import numpy as np
from modulator_analysis.modulator_evaluate import evaluate_params
from modulator_analysis.modulator_objective import objective_function

def fd_step(p, rel=0.03, abs_min=10e-9):
    """
    Relative finite-difference step with absolute floor.
    """
    return max(abs(p) * rel, abs_min)

def compute_fd_gradient(session, params, refs, opt_keys, weights=None):
    """
    Central finite difference gradient dJ/dp.
    """
    
    grads = {}

    for key in opt_keys:

        p0 = params[key]
        h = fd_step(p0)

        p_plus  = copy.deepcopy(params)
        p_minus = copy.deepcopy(params)

        p_plus[key]  = p0 + h
        p_minus[key] = p0 - h

        results_plus = evaluate_params(session, p_plus)
        Jp = objective_function(results_plus, refs, weights)
        results_minus = evaluate_params(session, p_minus)
        Jm = objective_function(results_minus, refs, weights)

        grads[key] = (Jp - Jm) / (2*h)

        print(f"[FD] {key}: h = {h*1e9:.1f} nm, grad = {grads[key]:.3e}")

    return grads

def update_params(params, grads, step_frac=0.05):
    """
    Gradient-descent-style update using relative step size.
    """

    new_params = params.copy()

    for key, grad in grads.items():
        if grad == 0:
            continue

        delta = step_frac * abs(params[key]) * np.sign(grad)
        new_params[key] -= delta

        print(f"[UPDATE] {key}: Δ = {-delta*1e9:.2f} nm")

    return new_params