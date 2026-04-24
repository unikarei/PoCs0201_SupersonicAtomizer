# Gas Diagnostics and Failure Criteria

This document describes diagnostics and failure criteria for the gas solver.

- **Nonphysical State Diagnostics**: report offending variables, axial location, and last valid state.
- **Branch Ambiguity Diagnostics**: surface ambiguity when the solver cannot select a consistent branch (subsonic vs supersonic) for the given geometry and boundary conditions.

Diagnostics should include actionable messages and recommended user steps.

- **Failed Closure Diagnostics**: when numerical closure (e.g., wall of equations or normal-shock closure) cannot be satisfied, surface a Failed Closure Diagnostics entry describing the offending variables and location.

- Include a classification entry named "Incomplete Solution Progression Diagnostics" to describe cases where solution assembly halts part-way and needs special reporting.

- Diagnostic reports should include a `last valid state summary` providing the last known consistent state (variables and axial location) for troubleshooting.