"""
modulator_objective.py
----------------------

Defines scalar objective J to minimize.

Default objective:

    J = w1 * (VpiL / VpiL_ref)
      + w2 * (loss / loss_ref)

Normalization ensures:
- Terms are dimensionless
- Baseline J ≈ 1

Weights allow:
- Pure efficiency optimization (loss weight = 0)
- Multi-objective tradeoff
"""

def objective_function(results, refs=None, weights=None):
    """
    Scalar objective to minimize.

    Parameters
    ----------
    results : dict
        Output of compute_modulator_overlap()
    refs : dict
        Reference values for normalization
    weights : dict
        Optional weighting of terms

    Returns
    -------
    J : float
        Objective value
    """

    if weights is None:
        weights = {
            "VpiL": 1.0,
            "loss": 0.0,
        }

    VpiL_Vcm = results["VpiL_Vcm"]
    loss_dB_per_cm = results["loss_dB_per_cm"]

    # Physical scaling (NOT starting design)
    V_scale = refs["VpiL_Vcm"]
    loss_scale = refs["loss_dB_per_cm"]

    V_term = VpiL_Vcm / V_scale
    loss_term = loss_dB_per_cm / loss_scale

    J = (weights["VpiL"] * V_term) + (weights["loss"] * loss_term)

    return J