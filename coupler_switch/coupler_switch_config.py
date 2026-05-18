WG_COUPLING_CONFIG = {
    "W": 350e-9, # waveguide width
    "H": 450e-9, # waveguide height
    
    "t_gap_pcm": 0e-9,  # gap between PCM and waveguide
    "t_pcm": 50e-9,      # PCM thickness
    "g": 250e-9,         # coupling gap between waveguides
    
    "x_coupler_center": 0, # x-center of coupler waveguide (to be set based on coupling direction)
    "x_bus_center": 0,     # x-center of bus waveguide (to be set based on coupling direction)
    "y_coupler_center": 0, # y-center of coupler waveguide (to be set based on coupling direction)
    "y_bus_center": 0,     # y-center of bus waveguide (to be set based on coupling direction)
    
    "pcm_mat_coupler": "SBS Amorphous",  # PCM material on coupler waveguide (active switching layer)
    "pcm_mat_bus": "SBS Crystalline",   # PCM material on bus waveguide (fixed layer)
    
    "coupling_direction": "vertical",  # "vertical" or "lateral"
    "pcm_loading_direction": "top_pcm",  # "side_pcm" or "top_pcm"
    
    "polarization": "TM",  # "TE" or "TM"
    "num_trial_modes": 6,  # number of trial modes for MODE solver
}