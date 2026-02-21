from modulator_analysis.modulator_lumapi import LumericalSession
from modulator_analysis.file_parsing_scripts.lumerical_electrostatics_mattocsv import convert_lumerical_electrostatics_to_csv
from modulator_analysis.file_parsing_scripts.lumerical_mode_mattocsv import convert_lumerical_mode_to_csv
from modulator_analysis.modulator_overlap import compute_modulator_overlap
from modulator_analysis.modulator_objective import objective_function


def evaluate_params(session, params, weights=None):
    """
    Full pipeline: params → Lumerical → metrics → objective
    """

    # 1. Run solvers
    session.run_simulation(params)

    # 2. Convert outputs
    convert_lumerical_electrostatics_to_csv(params["Vdc"])
    convert_lumerical_mode_to_csv()

    # 3. Compute metrics
    results = compute_modulator_overlap(params)

    # 4. Compute objective
    J = objective_function(results, weights)

    return J, results