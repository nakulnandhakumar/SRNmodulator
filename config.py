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

    # ---------------- electrostatics ----------------
    "Vdc": 100.0,

    # ---------------- SRN core ----------------
    "W": 450e-9,
    "H": 350e-9,

    # ---------------- electrode ----------------
    "metal_t": 100e-9,

    # ---------------- base geometry ----------------
    "g": g0,

    # base shield heights (NOT optimized)
    "t_shield_gapR": 0.5 * g0,
    "t_shield_gapL": 0.5 * g0,
    "t_shield_core": 0.5 * g0,
    "t_shield_metal": 0.5 * g0,

    # ---------------- segmentation deltas ----------------
    # left shield segments
    "dt_shield_gapL_1": 0.0,
    "dt_shield_gapL_2": 0.0,
    "dt_shield_gapL_3": 0.0,

    # right shield segments
    "dt_shield_gapR_1": 0.0,
    "dt_shield_gapR_2": 0.0,
    "dt_shield_gapR_3": 0.0,
}

# ============================================================
# Optimization variables
# ============================================================

OPT_KEYS = [
    "g",
    "t_shield_core",
    "t_shield_gapL",
    "t_shield_gapR",
    # "dt_shield_gapL_1",
    # "dt_shield_gapL_2",
    # "dt_shield_gapL_3",

    # "dt_shield_gapR_1",
    # "dt_shield_gapR_2",
    # "dt_shield_gapR_3",
]

# ============================================================
# Objective weights
# ============================================================

OBJECTIVE_WEIGHTS = {
    "VpiL": 1.0,
    "loss": 0.1,
}

# ============================================================
# Objective targets
# ============================================================

OBJECTIVE_TARGETS = {
    "VpiL_Vcm": 10.0,        # desired electro-optic efficiency
    "loss_dB_per_cm": 10.0,  # maximum acceptable optical loss
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
    "num_iterations": 3,
}

# ============================================================
# Random start bounds
# ============================================================

PARAM_BOUNDS = {

    # ------------------------------------------------
    # Electrode gap
    # ------------------------------------------------
    "g": (200e-9, 700e-9),

    # ------------------------------------------------
    # Base shield heights
    # ------------------------------------------------
    "t_shield_gapL": (50e-9, 500e-9),
    "t_shield_gapR": (50e-9, 500e-9),
    "t_shield_core": (50e-9, 600e-9),

    # ------------------------------------------------
    # Segmented shield deltas
    # actual height = base + delta
    # ------------------------------------------------
    "dt_shield_gapL_1": (-200e-9, 200e-9),
    "dt_shield_gapL_2": (-200e-9, 200e-9),
    "dt_shield_gapL_3": (-200e-9, 200e-9),

    "dt_shield_gapR_1": (-200e-9, 200e-9),
    "dt_shield_gapR_2": (-200e-9, 200e-9),
    "dt_shield_gapR_3": (-200e-9, 200e-9),
}