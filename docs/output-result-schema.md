# Output Result Schema

This document describes the `SimulationResult` schema for CSV/JSON/plotting consumers.

Required schema elements:

- `SimulationResult` object containing arrays and metadata
- axial coordinate `x`
- cross-sectional area `A`
- fields such as `pressure`, `temperature`, `density`, `working_fluid_velocity`, `Mach_number`
- droplet fields: `droplet_velocity`, `droplet_mean_diameter`, `droplet_maximum_diameter`, `Weber_number`
- include a **breakup event indicator** or flag per node to mark when breakup occurred.

List full field details, units, and metadata used by writers and plotters.

The `SimulationResult` structure also includes run-level **diagnostics** and `RunDiagnostics` metadata that capture warnings and failure context.