def objective_function(results, weights=None):
    """
    Scalar objective to minimize.

    Parameters
    ----------
    results : dict
        Output of compute_modulator_overlap()
    weights : dict
        Optional weighting of terms

    Returns
    -------
    J : float
        Objective value
    """

    if weights is None:
        weights = {
            "vpiL": 1.0,
            "loss": 0.0,   # add later
        }

    VpiL = results["VpiL_Vcm"]

    J = weights["vpiL"] * VpiL

    return J