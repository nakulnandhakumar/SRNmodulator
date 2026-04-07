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
    # ---------------- region materials ----------------
    "core_material_elect": "SRN_n3p1",
    "shield_material_elect": "HfO2",
    "BOX_cladding_material_elect": "SiO2",
    
    "core_material_mode": "SRN 3.1 (Silicon Rich Nitride)",
    "shield_material_mode": "HfO2",
    "BOX_cladding_material_mode": "SiO2 (Glass) - Palik",

    # ---------------- electrostatics ----------------
    "Vdc": 1.0,  # voltage for electrostatics simulation

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
    "loss": 5.0,
}

# ============================================================
# Objective targets
# ============================================================

OBJECTIVE_TARGETS = {
    "VpiL_true_Vcm": 10.0,        # desired electro-optic efficiency (Vdc = breakdown operating voltage)
    "loss_dB_per_cm": 5.0,    # maximum acceptable optical loss
}

# ============================================================
# Optimizer settings
# ============================================================

OPT_SETTINGS = {
    "alpha_init": 0.03,     # initial learning rate (step size multiplier for finite difference gradients)
    "rel_fd": 0.05,          # finite difference step relative to parameter value
    "abs_fd_min": 5e-9,
}

# ============================================================
# Experiment settings
# ============================================================

EXPERIMENT = {
    "random_starts": 3,
    "num_iterations": 6,
}

# ============================================================
# Random start variables and bounds
# ============================================================

RANDOM_KEYS = {
    "g",
    "t_shield_core",
    "t_shield_gapR",
    "t_shield_gapL",
}

PARAM_BOUNDS = {

    # ------------------------------------------------
    # Electrode gap
    # ------------------------------------------------
    "g": (750e-9, 850e-9),

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