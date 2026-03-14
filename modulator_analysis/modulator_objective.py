"""
modulator_objective.py
----------------------

Defines scalar objective J to minimize.

Objective:

    J = w_V * (VpiL / VpiL_target)
      + w_L * penalty(loss)

Loss penalty:
    if loss <= loss_target:
        penalty = 0
    else:
        penalty = ((loss - loss_target)/loss_target)^2
"""

from config import OBJECTIVE_TARGETS
from config import OBJECTIVE_WEIGHTS

def objective_function(results):
    """
    Scalar objective to minimize.
    """

    weight_VpiL = OBJECTIVE_WEIGHTS["VpiL"]
    weight_loss = OBJECTIVE_WEIGHTS["loss"]

    VpiL_Vcm = results["VpiL_Vcm"]
    loss_dB_per_cm = results["loss_dB_per_cm"]

    # targets
    V_target = OBJECTIVE_TARGETS["VpiL_Vcm"]
    loss_target = OBJECTIVE_TARGETS["loss_dB_per_cm"]

    # VpiL term
    V_term = VpiL_Vcm / V_target

    # loss penalty
    if loss_dB_per_cm <= loss_target:
        loss_penalty = 0.0
    else:
        loss_penalty = ((loss_dB_per_cm - loss_target) / loss_target) ** 2

    J = (weight_VpiL * V_term) + (weight_loss * loss_penalty)

    return J