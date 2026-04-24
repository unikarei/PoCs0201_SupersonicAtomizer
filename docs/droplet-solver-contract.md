# Droplet Solver Contract

This document describes the droplet solver inputs, outputs, and expected invariants.

Required runtime objects referenced:

- `AxialGrid`
- `GasSolution`
- `DropletSolution`

The droplet solver consumes `GasSolution` arrays and the `AxialGrid` to produce a `DropletSolution` with velocity and diameter histories aligned to the grid.

The droplet solver receives configuration from `DropletInjectionConfig` which provides initial injection values and optional loading parameters.

- The produced `DropletSolution` contains fields such as `droplet_velocity` aligned to grid nodes and reported in SI units.

- The solver also reports `slip_velocity` series used to compute drag and Weber-number diagnostics.

- The `DropletSolution` contains diameter fields such as `droplet_mean_diameter` and `droplet_maximum_diameter` recorded at each grid node.

- The `DropletSolution` also records breakup-related fields such as `Weber_number` and `breakup_flag` used for diagnostics and validation.