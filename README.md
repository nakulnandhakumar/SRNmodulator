# SRNmodulator
Repository to store code and data for SRN modulator project @ UCSD

## Code File Notes

## Data File Notes

### Lum_HfO2_ALDShield_reducedAu_VpiL.csv
<p> Contains data from Lumerical about the loss of modes propagating through a modulator which thin gold electrodes, an SRN core, and HfO2 shields which are deposited throudh ALD </p>

- <b>gap</b> <i>(nm)</i>: spacing between gold electrodes and core on both sides
- <b>loss(TE)</b> <i>(dB/cm)</i>: loss of the fundamental TE mode
- <b>loss(TM)</b> <i>(dB/cm)</i>: loss of the fundamental TM mode

### COMSOL_HfO2_ALDshield_reducedAu_acdc_field_dist.csv
<p> Contains spatially resolved electric field distributions extracted from COMSOL Multiphysics electrostatics simulations of the SRN modulator cross-section under both DC bias and small-signal AC excitation.

This dataset is used to compute electro-optic overlap integrals with optical mode profiles from Lumerical in order to evaluate the effective refractive index change 
and modulator efficiency</p>

- <b>x</b> <i>(m)</i>: horizontal spatial coordinate
- <b>y</b> <i>(m)</i>: vertical spatial coordinate
- <b>esAC.Ex</b> <i>(V/m)</i>: x-component of AC electric field (1 V drive, per-volt scaling)
- <b>esAC.Ey</b> <i>(V/m)</i>: y-component of AC electric field (1 V drive, per-volt scaling)
- <b>esDC.Ex</b> <i>(V/m)</i>: x-component of DC electric field (100 V DC bias applied to signal gold electrode)
- <b>esDC.Ey</b> <i>(V/m)</i>: y-component of DC electric field (100 V DC bias applied to signal gold electrode)