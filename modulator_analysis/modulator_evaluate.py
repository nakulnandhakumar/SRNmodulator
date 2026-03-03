"""
modulator_evaluate.py
---------------------

Single evaluation pipeline.

Input:
    params (dict of geometry + voltage)

Pipeline:
    1. Run Lumerical solvers
    2. Convert MAT → CSV
    3. Compute overlap integrals
    4. Return performance metrics

This function is intentionally stateless:
Each call performs a full simulation.

Returns:
    {
        VpiL_Vcm,
        loss_dB_per_cm,
        dneff_per_V,
        chi2_eff_avg,
        ...
    }

Note:
Objective is NOT computed here.
This file returns raw metrics only.
"""

from modulator_analysis.modulator_lumapi import LumericalSession
from modulator_analysis.file_parsing.lumerical_electrostatics_mattocsv import convert_lumerical_electrostatics_to_csv
from modulator_analysis.file_parsing.lumerical_mode_mattocsv import convert_lumerical_mode_to_csv
from modulator_analysis.modulator_overlap import compute_modulator_overlap
from modulator_analysis.modulator_objective import objective_function


def evaluate_params(session, params):
    """
    Full pipeline: params → Lumerical → metrics → objective
    """

    # 1. Run solvers
    session.run_simulation(params)

    # 2. Convert outputs
    convert_lumerical_electrostatics_to_csv(params["Vdc"])
    loss_dB_per_cm = convert_lumerical_mode_to_csv()

    # 3. Compute metrics
    results = compute_modulator_overlap(params)
    results["loss_dB_per_cm"] = loss_dB_per_cm

    return results