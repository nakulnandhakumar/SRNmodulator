import numpy as np


"""
Run a single simulation with the given configuration.
"""
def run_single(config, lum_project, lsf_script):

    # ============================================================
    # SIMULATION SETUP
    # ============================================================
    
    # Set wavelength in Lumerical
    lam = 1.55e-6
    
    lum_project.putv("lambda", lam)
    
    # Set number of trial modes for MODE solver
    num_trial_modes = config["num_trial_modes"]
    
    lum_project.putv("num_trial_modes", num_trial_modes)
    
    # ============================================================
    # GEOMETRY SETUP
    # ============================================================
    
    # Set waveguide geometry in Lumerical
    W_bus = config["W_bus"]
    H_bus = config["H_bus"]

    W_coupler = config["W_coupler"]
    H_coupler = config["H_coupler"]
    
    lum_project.putv("W_bus", W_bus)
    lum_project.putv("H_bus", H_bus)
    lum_project.putv("W_coupler", W_coupler)
    lum_project.putv("H_coupler", H_coupler)
    
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
    
    # Get coupling direction and pcm loading for later use
    coupling_direction = config["coupling_direction"]
    pcm_loading_direction = config["pcm_loading_direction"]
    
    # get polarization for later use
    polarization = config["polarization"]

    # ============================================================
    # RUN SIMULATION
    # ============================================================

    lum_project.eval(lsf_script)

    mode_data = []

    # ============================================================
    # EXTRACT MODE DATA
    # ============================================================
    
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
        
        # Select the relevant field component based on polarization for parity check later
        if polarization == "TE":
            Epar = Ex
        elif polarization == "TM":
            Epar = Ey
        else:
            raise ValueError(
                f"Unknown polarization: {polarization}"
            )

        margin = 20e-9
        buffer = 2e-9
        
        # ============================================================
        # UNIVERSAL WAVEGUIDE GEOMETRY
        # ============================================================

        # Waveguide centers
        x_coupler = x_coupler_center
        x_bus = x_bus_center

        y_coupler = y_coupler_center
        y_bus = y_bus_center

        # Core edges
        x_left_core_coupler = x_coupler - W_coupler/2
        x_right_core_coupler = x_coupler + W_coupler/2

        x_left_core_bus = x_bus - W_bus/2
        x_right_core_bus = x_bus + W_bus/2

        y_top_core_coupler = y_coupler + H_coupler/2
        y_bot_core_coupler = y_coupler - H_coupler/2

        y_top_core_bus = y_bus + H_bus/2
        y_bot_core_bus = y_bus - H_bus/2

        # ============================================================
        # LATERAL COUPLING
        # ============================================================

        if coupling_direction == "lateral":

            # ========================================================
            # SIDE PCM
            # ========================================================

            if pcm_loading_direction == "side_pcm":

                # PCM on RIGHT side of guides

                x_pcm_left_coupler  = x_right_core_coupler + t_gap_pcm
                x_pcm_right_coupler = x_pcm_left_coupler + t_pcm

                x_pcm_left_bus  = x_right_core_bus + t_gap_pcm
                x_pcm_right_bus = x_pcm_left_bus + t_pcm

                # SRN masks

                srn_mask_coupler = (
                    (X >= x_left_core_coupler - margin) &
                    (X <= x_right_core_coupler + margin) &
                    (Y >= y_bot_core_coupler - margin) &
                    (Y <= y_top_core_coupler + margin)
                )

                srn_mask_bus = (
                    (X >= x_left_core_bus - margin) &
                    (X <= x_right_core_bus + margin) &
                    (Y >= y_bot_core_bus - margin) &
                    (Y <= y_top_core_bus + margin)
                )

                # PCM masks

                mask_pcm_coupler = (
                    (X >= x_pcm_left_coupler) &
                    (X <= x_pcm_right_coupler) &
                    (Y >= y_bot_core_coupler - margin) &
                    (Y <= y_top_core_coupler + margin)
                )

                mask_pcm_bus = (
                    (X >= x_pcm_left_bus) &
                    (X <= x_pcm_right_bus) &
                    (Y >= y_bot_core_bus - margin) &
                    (Y <= y_top_core_bus + margin)
                )

            # ========================================================
            # TOP PCM
            # ========================================================

            elif pcm_loading_direction == "top_pcm":

                # PCM ABOVE guides

                y_pcm_bottom_coupler = y_top_core_coupler + t_gap_pcm
                y_pcm_top_coupler = y_pcm_bottom_coupler + t_pcm

                y_pcm_bottom_bus = y_top_core_bus + t_gap_pcm
                y_pcm_top_bus = y_pcm_bottom_bus + t_pcm

                # SRN masks

                srn_mask_coupler = (
                    (X >= x_left_core_coupler - margin) &
                    (X <= x_right_core_coupler + margin) &
                    (Y >= y_bot_core_coupler - margin) &
                    (Y <= y_top_core_coupler + margin)
                )

                srn_mask_bus = (
                    (X >= x_left_core_bus - margin) &
                    (X <= x_right_core_bus + margin) &
                    (Y >= y_bot_core_bus - margin) &
                    (Y <= y_top_core_bus + margin)
                )

                # PCM masks

                mask_pcm_coupler = (
                    (X >= x_left_core_coupler - margin) &
                    (X <= x_right_core_coupler + margin) &
                    (Y >= y_pcm_bottom_coupler) &
                    (Y <= y_pcm_top_coupler)
                )

                mask_pcm_bus = (
                    (X >= x_left_core_bus - margin) &
                    (X <= x_right_core_bus + margin) &
                    (Y >= y_pcm_bottom_bus) &
                    (Y <= y_pcm_top_bus)
                )

            else:
                raise ValueError(
                    f"Unknown PCM loading direction: "
                    f"{pcm_loading_direction}"
                )

        # ============================================================
        # VERTICAL COUPLING
        # ============================================================

        elif coupling_direction == "vertical":

            # ========================================================
            # SIDE PCM
            # ========================================================

            if pcm_loading_direction == "side_pcm":

                # PCM on RIGHT side of guides

                x_pcm_left_coupler  = x_right_core_coupler + t_gap_pcm
                x_pcm_right_coupler = x_pcm_left_coupler + t_pcm

                x_pcm_left_bus  = x_right_core_bus + t_gap_pcm
                x_pcm_right_bus = x_pcm_left_bus + t_pcm

                # ----------------------------------------------------
                # SRN masks
                # ----------------------------------------------------

                srn_mask_coupler = (
                    (X >= x_left_core_coupler - margin) &
                    (X <= x_right_core_coupler + margin) &
                    (Y >= y_bot_core_coupler - margin) &
                    (Y <= y_top_core_coupler + margin)
                )

                srn_mask_bus = (
                    (X >= x_left_core_bus - margin) &
                    (X <= x_right_core_bus + margin) &
                    (Y >= y_bot_core_bus - margin) &
                    (Y <= y_top_core_bus + margin)
                )

                # ----------------------------------------------------
                # PCM masks
                # ----------------------------------------------------

                mask_pcm_coupler = (
                    (X >= x_pcm_left_coupler) &
                    (X <= x_pcm_right_coupler) &
                    (Y >= y_bot_core_coupler - margin) &
                    (Y <= y_top_core_coupler + margin)
                )

                mask_pcm_bus = (
                    (X >= x_pcm_left_bus) &
                    (X <= x_pcm_right_bus) &
                    (Y >= y_bot_core_bus - margin) &
                    (Y <= y_top_core_bus + margin)
                )

            # ========================================================
            # TOP PCM
            # ========================================================

            elif pcm_loading_direction == "top_pcm":

                # PCM inside coupling gap:
                # - below top/coupler guide
                # - above bottom/bus guide

                y_pcm_top_coupler = y_bot_core_coupler - t_gap_pcm
                y_pcm_bottom_coupler = y_pcm_top_coupler - t_pcm

                y_pcm_bottom_bus = y_top_core_bus + t_gap_pcm
                y_pcm_top_bus = y_pcm_bottom_bus + t_pcm

                srn_mask_coupler = (
                    (X >= x_left_core_coupler - margin) &
                    (X <= x_right_core_coupler + margin) &
                    (Y >= y_bot_core_coupler - margin) &
                    (Y <= y_top_core_coupler + margin)
                )

                srn_mask_bus = (
                    (X >= x_left_core_bus - margin) &
                    (X <= x_right_core_bus + margin) &
                    (Y >= y_bot_core_bus - margin) &
                    (Y <= y_top_core_bus + margin)
                )

                mask_pcm_coupler = (
                    (X >= x_left_core_coupler - margin) &
                    (X <= x_right_core_coupler + margin) &
                    (Y >= y_pcm_bottom_coupler) &
                    (Y <= y_pcm_top_coupler)
                )

                mask_pcm_bus = (
                    (X >= x_left_core_bus - margin) &
                    (X <= x_right_core_bus + margin) &
                    (Y >= y_pcm_bottom_bus) &
                    (Y <= y_pcm_top_bus)
                )
            
            # ========================================================
            # ASYMMETRIC TOP PCM
            # ========================================================

            elif pcm_loading_direction == "asym_pcm":
                
                # PCM inside coupling gap, but only on coupler side:
                # - below top/coupler guide

                y_pcm_top_coupler = y_bot_core_coupler - t_gap_pcm
                y_pcm_bottom_coupler = y_pcm_top_coupler - t_pcm

                srn_mask_coupler = (
                    (X >= x_left_core_coupler - margin) &
                    (X <= x_right_core_coupler + margin) &
                    (Y >= y_bot_core_coupler - margin) &
                    (Y <= y_top_core_coupler + margin)
                )

                srn_mask_bus = (
                    (X >= x_left_core_bus - margin) &
                    (X <= x_right_core_bus + margin) &
                    (Y >= y_bot_core_bus - margin) &
                    (Y <= y_top_core_bus + margin)
                )

                mask_pcm_coupler = (
                    (X >= x_left_core_coupler - margin) &
                    (X <= x_right_core_coupler + margin) &
                    (Y >= y_pcm_bottom_coupler) &
                    (Y <= y_pcm_top_coupler)
                )

                mask_pcm_bus = np.zeros_like(mask_pcm_coupler, dtype=bool)

            else:
                raise ValueError(
                    f"Unknown PCM loading direction: "
                    f"{pcm_loading_direction}"
                )
        
        else:
            raise ValueError(
                f"Unknown coupling direction: {coupling_direction}"
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
        
        # ============================================================
        # PARITY CHECK
        # ============================================================

        field_coupler = np.sum(np.real(Epar) * srn_mask_coupler)
        field_bus = np.sum(np.real(Epar) * srn_mask_bus)

        parity = field_coupler * field_bus

        if parity > 0:
            parity_label = "symmetric"
        else:
            parity_label = "antisymmetric"

        mode_data.append({
            "mode": m,
            "neff": neff,
            "TEfrac": TEfrac,
            
            "parity": parity,
            "parity_label": parity_label,
            
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
    
    # Warn if selected modes have same parity, which may lead to weak coupling and low extinction ratio
    if m1["parity"] * m2["parity"] > 0:
        print(
            f"WARNING: selected modes have same parity: "
            f"mode {m1['mode']} = {m1['parity_label']}, "
            f"mode {m2['mode']} = {m2['parity_label']}"
        )
    
    # Not implemented yet: more advanced supermode pairing based on parity and 
    # SRN confinement, instead of just neff proximity
    """
    # ============================================================
    # PARITY-BASED SUPERMODE PAIRING
    # ============================================================

    sym_modes = []
    antisym_modes = []

    # Classify modes into symmetric and antisymmetric based on parity
    for md in valid:
        if md["parity"] > 0:
            sym_modes.append(md)
        elif md["parity"] < 0:
            antisym_modes.append(md)

    # Make sure both parity families exist
    if len(sym_modes) == 0 or len(antisym_modes) == 0:
        print(
            f"ERROR: could not find both symmetric "
            f"and antisymmetric {polarization} modes"
        )
        return None

    # Sort by SRN confinement
    sym_modes = sorted(
        sym_modes,
        key=lambda x: x["eta_srn_total"],
        reverse=True
    )

    antisym_modes = sorted(
        antisym_modes,
        key=lambda x: x["eta_srn_total"],
        reverse=True
    )

    # Fundamental supermode pair
    m1 = sym_modes[0]
    m2 = antisym_modes[0]
    
    # Diagnostic printout of selected modes
    print(
        f"\nSelected supermode pair:"
    )
    print(
        f"m1 = mode {m1['mode']} | "
        f"{m1['parity_label']} | "
        f"neff = {m1['neff']:.6f} | "
        f"TEfrac = {m1['TEfrac']:.3f}"
    )
    print(
        f"m2 = mode {m2['mode']} | "
        f"{m2['parity_label']} | "
        f"neff = {m2['neff']:.6f} | "
        f"TEfrac = {m2['TEfrac']:.3f}"
    )
    """

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
        
        "TEfrac1": m1["TEfrac"],
        "TEfrac2": m2["TEfrac"],
        "polarization": polarization,
        
        "parity1": m1["parity"],
        "parity2": m2["parity"],
        "parity_label1": m1["parity_label"],
        "parity_label2": m2["parity_label"],
    }