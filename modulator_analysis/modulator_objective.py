def objective_function(results, loss_dB_per_cm, weights=None):
    """
    Scalar objective to minimize.

    Parameters
    ----------
    results : dict
        Output of compute_modulator_overlap()
    loss_dB_per_cm : float
        Mode loss in dB/cm
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
            "loss": 0.0,   # add later
        }

    VpiL = results["VpiL_Vcm"]

    J = (weights["VpiL"] * VpiL) + (weights["loss"] * loss_dB_per_cm)

    return J