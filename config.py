"""
config.py
---------

Central configuration for SRN modulator optimization experiments.
"""

# ============================================================
# Device + geometry parameters
# ============================================================

g0 = 600e-9

PARAMS = {
    # electrostatics
    "Vdc": 100.0,

    # SRN core
    "W": 450e-9,
    "H": 350e-9,

    # electrode
    "metal_t": 100e-9,

    # geometry parameters
    "g": g0,
    "t_shield_gapR": 0.5 * g0,
    "t_shield_gapL": 0.5 * g0,
    "t_shield_core": 0.5 * g0,
    "t_shield_metal": 0.5 * g0,
}

# ============================================================
# Optimization variables
# ============================================================

OPT_KEYS = [
    "g",
    "t_shield_gapR",
    "t_shield_gapL",
    "t_shield_core",
]

# ============================================================
# Objective weights
# ============================================================

OBJECTIVE_WEIGHTS = {
    "VpiL": 1.0,
    "loss": 0.05,
}

# ============================================================
# Optimizer settings
# ============================================================

OPT_SETTINGS = {
    "alpha_init": 0.06,
    "rel_fd": 0.1,
    "abs_fd_min": 5e-9,
}

# ============================================================
# Experiment settings
# ============================================================

EXPERIMENT = {
    "random_starts": 5,
    "num_iterations": 6,
}

# ============================================================
# Random start bounds
# ============================================================

PARAM_BOUNDS = {

    # electrode gap
    "g": (200e-9, 700e-9),

    # shield geometry
    "t_shield_gapR": (10e-9, 500e-9),
    "t_shield_gapL": (10e-9, 500e-9),
    "t_shield_core": (10e-9, 500e-9),
}