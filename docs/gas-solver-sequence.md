```markdown
# Gas Solver Sequence

This document describes the step-by-step gas solver execution sequence used by the application.

Summary steps:

- receive validated inputs (geometry, grid, inlet total conditions, outlet static pressure)
- initialize inlet-side state representation
- select branch (subsonic/supersonic/choked)
- march along `AxialGrid` and assemble gas-state arrays

Detailed phrasing: the solver will advance or assemble gas states node-by-node using thermo-provider queries and geometry-area lookups (advance or assemble gas states).

Include pseudocode and branching notes for choked and Laval nozzle cases.

The solver computes and records the **Mach number** at each axial node as part of the assembled gas-state arrays.

- The solver returns a structured `GasSolution` object containing arrays of pressure, temperature, density, velocity and Mach number aligned to the `AxialGrid`.

- The solver also emits diagnostics and run-level summaries for downstream reporting and validation (diagnostics).
```
```markdown
# Gas Solver Sequence

This document describes the step-by-step gas solver execution sequence used by the application.

Summary steps:

- receive validated inputs (geometry, grid, inlet total conditions, outlet static pressure)
- initialize inlet-side state representation
- select branch (subsonic/supersonic/choked)
- march along `AxialGrid` and assemble gas-state arrays

Detailed phrasing: the solver will advance or assemble gas states node-by-node using thermo-provider queries and geometry-area lookups (advance or assemble gas states).

Include pseudocode and branching notes for choked and Laval nozzle cases.

The solver computes and records the **Mach number** at each axial node as part of the assembled gas-state arrays.

- The solver returns a structured `GasSolution` object containing arrays of pressure, temperature, density, velocity and Mach number aligned to the `AxialGrid`.
```
# Gas Solver Sequence

This document describes the step-by-step gas solver execution sequence used by the application.

Summary steps:

- receive validated inputs (geometry, grid, inlet total conditions, outlet static pressure)
- initialize inlet-side state representation
- select branch (subsonic/supersonic/choked)
 The solver computes and records the **Mach number** at each axial node as part of the assembled gas-state arrays.
 
 - The solver returns a structured `GasSolution` object containing arrays of pressure, temperature, density, velocity and Mach number aligned to the `AxialGrid`.

Include pseudocode and branching notes for choked and Laval nozzle cases.

The solver computes and records the **Mach number** at each axial node as part of the assembled gas-state arrays.