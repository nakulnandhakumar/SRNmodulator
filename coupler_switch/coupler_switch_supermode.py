import numpy as np

# ===================== CORE FUNCTION =====================

def run_single(config, lum_project, lsf_script):

    # Set wavelength in Lumerical
    lam = 1.55e-6
    
    lum_project.putv("lambda", lam)
    
    # Set number of trial modes for MODE solver
    num_trial_modes = config["num_trial_modes"]
    
    lum_project.putv("num_trial_modes", num_trial_modes)
    
    # Set waveguide geometry in Lumerical
    W = config["W"]
    H = config["H"]
    
    lum_project.putv("W", W)
    lum_project.putv("H", H)
    
    # Set PCM geometry in Lumerical
    g = config["g"]
    t_gap_pcm = config["t_gap_pcm"]
    t_pcm = config["t_pcm"]
    
    lum_project.putv("g", g)
    lum_project.putv("t_gap_pcm", t_gap_pcm)
    lum_project.putv("t_pcm", t_pcm)
    
    # Set PCM states in Lumerical
    pcm_material_coupler = config["pcm_mat_coupler"]
    pcm_material_bus = config["pcm_mat_bus"]
    
    lum_project.putv("pcm_mat_coupler", pcm_material_coupler)   # PCM on coupler waveguide
    lum_project.putv("pcm_mat_bus", pcm_material_bus)           # PCM on bus waveguide
    
    # Set waveguide centers from config
    x_coupler_center = config["x_coupler_center"]
    x_bus_center = config["x_bus_center"]
    y_coupler_center = config["y_coupler_center"]
    y_bus_center = config["y_bus_center"]
    
    lum_project.putv("x_coupler_center", x_coupler_center)
    lum_project.putv("x_bus_center", x_bus_center)
    lum_project.putv("y_coupler_center", y_coupler_center)
    lum_project.putv("y_bus_center", y_bus_center)
    
    # Get coupling direction for later use
    coupling_direction = config["coupling_direction"]

    # Evaluate the Lumerical script to compute modes and coupling parameters
    lum_project.eval(lsf_script)

    mode_data = []

    for m in range(1, num_trial_modes+1):
        name = f"mode{m}"

        try:
            lum_project.eval(f'neff_temp = real(getdata("FDE::data::{name}", "neff"));')
            neff = lum_project.getv("neff_temp")

            lum_project.eval(f'TEfrac_temp = getdata("FDE::data::{name}", "TE polarization fraction");')
            TEfrac = lum_project.getv("TEfrac_temp")

            lum_project.eval(f'x_temp = getdata("FDE::data::{name}", "x");')
            x = np.squeeze(lum_project.getv("x_temp"))

            lum_project.eval(f'y_temp = getdata("FDE::data::{name}", "y");')
            y = np.squeeze(lum_project.getv("y_temp"))

            lum_project.eval(f'Ex_temp = getdata("FDE::data::{name}", "Ex");')
            Ex = np.squeeze(lum_project.getv("Ex_temp"))

            lum_project.eval(f'Ey_temp = getdata("FDE::data::{name}", "Ey");')
            Ey = np.squeeze(lum_project.getv("Ey_temp"))

            lum_project.eval(f'Ez_temp = getdata("FDE::data::{name}", "Ez");')
            Ez = np.squeeze(lum_project.getv("Ez_temp"))
            
            lum_project.eval(f'loss_temp = real(getdata("FDE::data::{name}", "loss"));')
            loss_dB_m = lum_project.getv("loss_temp")    # dB/m
            loss_dB_cm = loss_dB_m / 100  # dB/cm

        except:
            print(f"WARNING: failed to get data for mode {m}")
            continue

        X, Y = np.meshgrid(x, y, indexing='ij')
        E2 = np.abs(Ex)**2 + np.abs(Ey)**2 + np.abs(Ez)**2

        margin = 20e-9
        buffer = 2e-9

        # ============================================================
        # LATERAL COUPLING
        # ============================================================

        if coupling_direction == "lateral":

            # --------------------------------
            # Waveguide centers
            # --------------------------------

            x_coupler = x_coupler_center
            x_bus     = x_bus_center

            y_coupler = y_coupler_center
            y_bus     = y_bus_center

            # ========================================================
            # COUPLER WG
            # ========================================================

            y_top_core_coupler = y_coupler + H/2
            y_bot_core_coupler = y_coupler - H/2

            y_pcm_bottom_coupler = y_top_core_coupler + t_gap_pcm
            y_pcm_top_coupler    = y_pcm_bottom_coupler + t_pcm

            y_mask_top_candidate_coupler = y_top_core_coupler + margin
            y_pcm_limit_coupler = y_pcm_bottom_coupler - buffer

            if t_gap_pcm <= buffer:
                y_mask_top_coupler = y_top_core_coupler
            else:
                y_mask_top_coupler = min(
                    y_mask_top_candidate_coupler,
                    y_pcm_limit_coupler
                )

            # ========================================================
            # BUS WG
            # ========================================================

            y_top_core_bus = y_bus + H/2
            y_bot_core_bus = y_bus - H/2

            y_pcm_bottom_bus = y_top_core_bus + t_gap_pcm
            y_pcm_top_bus    = y_pcm_bottom_bus + t_pcm

            y_mask_top_candidate_bus = y_top_core_bus + margin
            y_pcm_limit_bus = y_pcm_bottom_bus - buffer

            if t_gap_pcm <= buffer:
                y_mask_top_bus = y_top_core_bus
            else:
                y_mask_top_bus = min(
                    y_mask_top_candidate_bus,
                    y_pcm_limit_bus
                )

            # --------------------------------
            # SRN masks
            # --------------------------------

            srn_mask_coupler = (
                (X >= x_coupler - W/2 - margin) &
                (X <= x_coupler + W/2 + margin) &
                (Y >= y_bot_core_coupler - margin) &
                (Y <= y_mask_top_coupler)
            )

            srn_mask_bus = (
                (X >= x_bus - W/2 - margin) &
                (X <= x_bus + W/2 + margin) &
                (Y >= y_bot_core_bus - margin) &
                (Y <= y_mask_top_bus)
            )

            # --------------------------------
            # PCM masks
            # --------------------------------

            mask_pcm_coupler = (
                (X >= x_coupler - W/2 - margin) &
                (X <= x_coupler + W/2 + margin) &
                (Y >= y_pcm_bottom_coupler) &
                (Y <= y_pcm_top_coupler)
            )

            mask_pcm_bus = (
                (X >= x_bus - W/2 - margin) &
                (X <= x_bus + W/2 + margin) &
                (Y >= y_pcm_bottom_bus) &
                (Y <= y_pcm_top_bus)
            )

        # ============================================================
        # VERTICAL COUPLING
        # ============================================================

        elif coupling_direction == "vertical":

            # --------------------------------
            # Waveguide centers
            # --------------------------------

            x_coupler = x_coupler_center
            x_bus     = x_bus_center

            y_coupler = y_coupler_center
            y_bus     = y_bus_center

            # ========================================================
            # COUPLER WG
            # ========================================================

            x_right_core_coupler = x_coupler + W/2
            x_left_core_coupler  = x_coupler - W/2

            x_pcm_left_coupler  = x_right_core_coupler + t_gap_pcm
            x_pcm_right_coupler = x_pcm_left_coupler + t_pcm

            x_mask_right_candidate_coupler = (
                x_right_core_coupler + margin
            )

            x_pcm_limit_coupler = x_pcm_left_coupler - buffer

            if t_gap_pcm <= buffer:
                x_mask_right_coupler = x_right_core_coupler
            else:
                x_mask_right_coupler = min(
                    x_mask_right_candidate_coupler,
                    x_pcm_limit_coupler
                )

            # ========================================================
            # BUS WG
            # ========================================================

            x_right_core_bus = x_bus + W/2
            x_left_core_bus  = x_bus - W/2

            x_pcm_left_bus  = x_right_core_bus + t_gap_pcm
            x_pcm_right_bus = x_pcm_left_bus + t_pcm

            x_mask_right_candidate_bus = (
                x_right_core_bus + margin
            )

            x_pcm_limit_bus = x_pcm_left_bus - buffer

            if t_gap_pcm <= buffer:
                x_mask_right_bus = x_right_core_bus
            else:
                x_mask_right_bus = min(
                    x_mask_right_candidate_bus,
                    x_pcm_limit_bus
                )

            # --------------------------------
            # SRN masks
            # --------------------------------

            srn_mask_coupler = (
                (X >= x_left_core_coupler - margin) &
                (X <= x_mask_right_coupler) &
                (Y >= y_coupler - H/2 - margin) &
                (Y <= y_coupler + H/2 + margin)
            )

            srn_mask_bus = (
                (X >= x_left_core_bus - margin) &
                (X <= x_mask_right_bus) &
                (Y >= y_bus - H/2 - margin) &
                (Y <= y_bus + H/2 + margin)
            )

            # --------------------------------
            # PCM masks
            # --------------------------------

            mask_pcm_coupler = (
                (X >= x_pcm_left_coupler) &
                (X <= x_pcm_right_coupler) &
                (Y >= y_coupler - H/2 - margin) &
                (Y <= y_coupler + H/2 + margin)
            )

            mask_pcm_bus = (
                (X >= x_pcm_left_bus) &
                (X <= x_pcm_right_bus) &
                (Y >= y_bus - H/2 - margin) &
                (Y <= y_bus + H/2 + margin)
            )

        # =====================
        # Energy fractions
        # =====================

        E_total = np.sum(E2)

        eta_coupler  = np.sum(E2 * srn_mask_coupler)  / E_total
        eta_bus = np.sum(E2 * srn_mask_bus) / E_total
        
        eta_pcm_coupler  = np.sum(E2 * mask_pcm_coupler) / E_total
        eta_pcm_bus = np.sum(E2 * mask_pcm_bus) / E_total
        
        eta_srn_total = eta_coupler + eta_bus
        eta_pcm_total = eta_pcm_coupler + eta_pcm_bus

        mode_data.append({
            "mode": m,
            "neff": neff,
            "TEfrac": TEfrac,
            "loss_dB_cm": loss_dB_cm,
            "eta_coupler": eta_coupler,
            "eta_bus": eta_bus,
            "eta_srn_total": eta_srn_total,
            "eta_pcm_coupler": eta_pcm_coupler,
            "eta_pcm_bus": eta_pcm_bus,
            "eta_pcm_total": eta_pcm_total
        })
        
        # print(f"\nMode {m}")
        # print(f"neff = {neff:.6f}")
        # print(f"TEfrac = {TEfrac:.3f}")
        # print(f"eta_coupler  = {eta_coupler:.3f}")
        # print(f"eta_bus = {eta_bus:.3f}")
        # print(f"eta_pcm   = {eta_pcm:.3f}")
        # print(f"eta_srn_total = {eta_srn_total:.3f}")

    # =====================
    # MODE SELECTION
    # =====================

    polarization = config["polarization"]

    valid = []

    for md in mode_data:

        # --------------------------------------------------------
        # Polarization filtering
        # --------------------------------------------------------

        if polarization == "TE":
            polarization_valid = md["TEfrac"] > 0.9

        elif polarization == "TM":
            polarization_valid = md["TEfrac"] < 0.1

        else:
            raise ValueError(
                f'Unknown polarization: {polarization}'
            )

        # --------------------------------------------------------
        # PCM overlap filtering
        # --------------------------------------------------------

        pcm_valid = (
            md["eta_pcm_coupler"] < 0.15 and
            md["eta_pcm_bus"] < 0.15
        )

        # --------------------------------------------------------
        # Final validity
        # --------------------------------------------------------

        if polarization_valid and pcm_valid:
            valid.append(md)

    if len(valid) < 2:
        print(
            f"ERROR: not enough valid {polarization} modes"
        )
        return None

    modes = sorted(valid, key=lambda x: x["neff"], reverse=True)

    m1 = modes[0]
    m2 = modes[1]

    # =====================
    # PHYSICS
    # =====================

    dneff = abs(m1["neff"] - m2["neff"])
    Omega = (np.pi / lam) * dneff

    # Detuning proxy
    D = abs(m1["eta_bus"] - m2["eta_bus"])

    A_max = 1 - D**2
    
    # Effective loss (weighted by excitation)
    loss1 = m1["loss_dB_cm"]
    loss2 = m2["loss_dB_cm"]

    # excitation weights (input waveguide)
    w1 = m1["eta_bus"]
    w2 = m2["eta_bus"]

    norm = w1 + w2 + 1e-15
    w1 /= norm
    w2 /= norm

    loss_eff = w1 * loss1 + w2 * loss2   # dB/cm

    return {
        "neff1": m1["neff"],
        "neff2": m2["neff"],
        "dneff": dneff,
        "Omega": Omega,
        "D": D,
        "A_max": A_max,
        
        "eta_coupler_1": m1["eta_coupler"],
        "eta_bus_1": m1["eta_bus"],
        "eta_pcm_coupler_1": m1["eta_pcm_coupler"],
        "eta_pcm_bus_1": m1["eta_pcm_bus"],

        "eta_coupler_2": m2["eta_coupler"],
        "eta_bus_2": m2["eta_bus"],
        "eta_pcm_coupler_2": m2["eta_pcm_coupler"],
        "eta_pcm_bus_2": m2["eta_pcm_bus"],

        "eta_pcm_avg": 0.5 * (m1["eta_pcm_total"] + m2["eta_pcm_total"]),
        
        "loss1": loss1,
        "loss2": loss2,
        "loss_eff": loss_eff,
        
        "mode1": m1["mode"],
        "mode2": m2["mode"],
    }