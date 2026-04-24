# Gas Solver Inputs and Outputs

This document lists required inputs and expected outputs for the gas solver.

Required inputs:

- `AxialGrid`
- `GeometryModel`
- boundary conditions: `Pt_in`, `Tt_in`, `Ps_out`

Expected outputs: axial arrays for pressure, temperature, density, working fluid velocity, and Mach number.

All arrays are aligned to `AxialGrid` node positions and expressed in SI units.

Field names used in result schemas include `mach_number` (lowercase) to match CSV/JSON column keys.