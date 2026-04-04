# Supersonic Atomizer Simulator Specification

## 1. Purpose

This project will deliver a Python-based engineering simulator for atomization of water droplets in a quasi-1D internal compressible flow duct or nozzle.

The simulator is intended for research and early-stage engineering studies, not for high-fidelity production CFD. Its purpose is to predict, along the axial direction $x$:

- working-fluid flow evolution,
- droplet acceleration due to gas-liquid slip,
- simple droplet breakup onset and diameter reduction,
- key derived indicators such as Weber number and Mach number,
- plotted and exportable results for case comparison and sensitivity studies.

The first release shall prioritize numerical robustness, modularity, traceability of assumptions, and ease of future extension.

---

## 2. Scope

### 2.1 In Scope for MVP

The MVP shall cover the following:

- Steady quasi-1D compressible internal flow along the $x$-axis
- User-supplied area distribution $A(x)$
- Working fluid selection:
  - air
  - steam
- Steam support designed around an IF97-based thermodynamic property abstraction
- Equilibrium steam assumption for the first release
- Water droplet transport using a representative droplet model
- Slip-velocity-based droplet acceleration
- Simple breakup criterion based on a Weber number threshold
- Evolution of at least:
  - working fluid velocity,
  - droplet velocity,
  - droplet mean diameter,
  - droplet maximum diameter,
  - Weber number,
  - pressure,
  - temperature,
  - Mach number
- YAML input file support
- CLI execution
- CSV and JSON result export
- Matplotlib-based plotting of major quantities versus $x$

### 2.2 Scope Intent

The MVP is specifically focused on quasi-1D internal flow plus droplet transport plus simple breakup. It is intended to provide a maintainable baseline architecture for later extensions such as improved steam models, stronger two-phase coupling, richer breakup models, and validation utilities.

---

## 3. Out of Scope

The following are explicitly out of scope for the MVP:

- 3D CFD
- 2D/3D internal flow field resolution
- droplet-droplet collision
- droplet coalescence
- wall-film physics
- wall deposition / rebound / splashing models
- detailed free jet external field
- plate impingement
- non-equilibrium condensation
- high-fidelity turbulence modeling
- full droplet size distribution transport
- LES / RANS / DNS treatment
- shock-resolving multiphase CFD
- conjugate heat transfer
- optimization workflow automation
- GUI application

These items may be considered in later releases only after the MVP is validated.

---

## 4. Users and Use Cases

### 4.1 Target Users

- Researchers studying droplet breakup in compressible internal flows
- Engineers comparing nozzle or duct area profiles
- Developers extending thermodynamic or breakup submodels
- Analysts performing sensitivity studies on operating conditions

### 4.2 Primary Use Cases

- Run a single quasi-1D case from a YAML configuration file using a CLI
- Compare atomization behavior between air and steam cases
- Examine how outlet static pressure affects gas acceleration and droplet breakup
- Compare different inlet droplet conditions
- Compare different area distributions $A(x)$
- Export computed fields for post-processing and reporting
- Plot major solution variables against axial position

---

## 5. Functional Requirements

### 5.1 Input Handling

- [ ] The simulator shall accept case configuration from a YAML input file.
- [ ] The simulator shall accept user-defined area distribution $A(x)$.
- [ ] The simulator shall accept inlet total pressure.
- [ ] The simulator shall accept inlet total temperature.
- [ ] The simulator shall accept outlet static pressure.
- [ ] The simulator shall accept working fluid selection as air or steam.
- [ ] The simulator shall accept optional inlet wetness for steam cases.
- [ ] The simulator shall accept droplet injection conditions.

### 5.2 Flow Simulation

- [ ] The simulator shall solve a steady quasi-1D compressible flow problem along the axial coordinate.
- [ ] The simulator shall compute axial distributions of pressure, temperature, density, velocity, and Mach number.
- [ ] The simulator shall support a fluid property abstraction that allows air and steam implementations.
- [ ] The steam implementation shall be designed to support IF97-based properties.
- [ ] The first release shall assume equilibrium steam behavior.

### 5.3 Droplet Simulation

- [ ] The simulator shall compute droplet velocity evolution along $x$.
- [ ] The simulator shall compute droplet mean diameter evolution along $x$.
- [ ] The simulator shall compute droplet maximum diameter evolution along $x$.
- [ ] The simulator shall compute slip velocity between working fluid and droplets.
- [ ] The simulator shall compute droplet Weber number along $x$.
- [ ] The simulator shall apply a simple breakup criterion when Weber number exceeds a defined threshold.
- [ ] The simulator shall update droplet diameter metrics after breakup events according to the selected MVP breakup rule.

### 5.4 Outputs

- [ ] The simulator shall export numerical results to CSV.
- [ ] The simulator shall export numerical results to JSON.
- [ ] The simulator shall generate plots of major quantities versus $x$ using Matplotlib.
- [ ] The simulator shall provide run status and error information through the CLI.

### 5.5 Software Structure

- [ ] The software shall be structured to separate physics, solver, IO, plotting, validation, and configuration concerns.
- [ ] The software shall be written in Python only.
- [ ] The software shall be organized for testability and future extension.

---

## 6. Non-Functional Requirements

### 6.1 Maintainability

- Clear separation of modules for physics, numerics, IO, plotting, validation, and CLI
- Small, composable components with explicit interfaces
- Limited hidden state
- Documentation of assumptions and model limitations

### 6.2 Numerical Robustness

- Numerical robustness shall take priority over feature count.
- The solver shall prefer stable and traceable methods over aggressive optimization.
- Failure modes shall be detectable and reported clearly.

### 6.3 Testability

- Core physics and solver logic shall be testable without plotting or CLI dependencies.
- Deterministic test cases shall be possible from fixed YAML inputs.
- Validation cases shall be definable independently from production case files.

### 6.4 Usability

- The simulator shall run from VS Code and standard Python CLI workflows.
- Input and output formats shall be human-readable.
- Units shall be SI throughout.

### 6.5 Extensibility

- The architecture shall allow future replacement of the steam property backend.
- The breakup model shall be replaceable without rewriting the solver core.
- The fluid model shall be abstracted so additional working fluids can be added later.

---

## 7. Inputs

### 7.1 Required Inputs

| Name | Description | Unit | Notes |
|---|---|---:|---|
| `working_fluid` | Working fluid identifier | - | `air` or `steam` |
| `Pt_in` | Inlet total pressure | Pa | Required |
| `Tt_in` | Inlet total temperature | K | Required |
| `Ps_out` | Outlet static pressure | Pa | Required |
| `A(x)` | Area distribution along axis | $m^2$ | User-defined profile |
| `x` grid definition | Axial extent and discretization | m, - | Required |
| `droplet_velocity_in` | Initial droplet velocity | m/s | Required |
| `droplet_diameter_mean_in` | Initial mean droplet diameter | m | Required |
| `droplet_diameter_max_in` | Initial maximum droplet diameter | m | Required |

### 7.2 Optional Inputs

| Name | Description | Unit | Notes |
|---|---|---:|---|
| `inlet_wetness` | Inlet wetness for steam | - | Optional, mainly for steam |
| `water_mass_flow_rate` | Injected droplet mass flow rate | kg/s | Optional if another equivalent loading metric is defined later |
| `critical_weber_number` | Breakup threshold | - | Required by breakup model if not defaulted |
| `breakup_factor_mean` | Mean diameter reduction factor | - | Model parameter |
| `breakup_factor_max` | Maximum diameter reduction factor | - | Model parameter |
| `drag_model` | Droplet drag model selector | - | MVP default shall be simple spherical drag |
| `steam_property_model` | Steam property backend | - | Designed for IF97 |

### 7.3 Input Format Requirements

- Input shall be provided through YAML.
- Units shall be SI.
- Area distribution shall be accepted at minimum as tabulated $(x, A)$ data.
- Input schema shall be documented and validated.

---

## 8. Outputs

### 8.1 Primary Axial Outputs

The simulator shall provide the following as functions of $x$:

- `x`
- `A`
- `pressure`
- `temperature`
- `density`
- `working_fluid_velocity`
- `Mach_number`
- `droplet_velocity`
- `slip_velocity`
- `droplet_mean_diameter`
- `droplet_maximum_diameter`
- `Weber_number`

### 8.2 Additional Useful Outputs for MVP

The MVP should also provide, where available:

- breakup event indicator or flag
- derived droplet Reynolds number
- metadata describing selected models and run settings
- summary information for convergence or failure status

### 8.3 Output Formats

- CSV for tabular numeric data
- JSON for structured results and metadata
- PNG or similar static plot files generated through Matplotlib

### 8.4 Plotting Requirements

At minimum, the simulator shall plot versus $x$:

- pressure
- temperature
- working fluid velocity
- droplet velocity
- Mach number
- droplet mean diameter
- droplet maximum diameter
- Weber number

---

## 9. Physics Assumptions

### 9.1 Flow Assumptions

- Steady flow
- Quasi-1D flow along the duct/nozzle centerline coordinate
- Cross-sectional averaging is acceptable for the MVP
- The working fluid is represented as a single effective gas phase in the quasi-1D solver
- Area change is prescribed and does not deform during simulation

### 9.2 Working Fluid Assumptions

For air:

- Air may be treated as an ideal gas in the MVP.
- Constant or simply parameterized thermophysical properties are acceptable for the MVP if documented.

For steam:

- Steam support shall be designed around IF97-based property handling.
- The first release shall assume equilibrium steam.
- The first release may limit steam calculations to the subset of states and property calls required by the approved MVP cases.

### 9.3 Droplet Assumptions

- Droplets are water droplets.
- Droplets are represented by one or more bulk/representative quantities rather than a full population balance.
- Droplet transport is evaluated along the same axial coordinate as the gas solution.
- Droplet acceleration is driven primarily by aerodynamic drag and slip velocity.
- Droplet shape deformation is not resolved explicitly in the MVP.

### 9.4 Breakup Assumptions

- Breakup is represented by a simple threshold model based on Weber number.
- When $We > We_{crit}$, droplet diameter metrics are reduced by a prescribed rule.
- The MVP does not attempt to resolve breakup mode maps, fragment distributions, or breakup time-scale physics in detail.

### 9.5 Excluded Physics Assumptions

The MVP shall not model:

- droplet-droplet collision/coalescence,
- wall-film formation,
- non-equilibrium condensation,
- detailed external jet development,
- plate impingement,
- high-fidelity turbulence interactions.

---

## 10. Numerical Assumptions

- The solution domain is discretized along $x$ only.
- The gas solver uses a quasi-1D compressible formulation appropriate for steady internal flow.
- The droplet model is advanced consistently along the axial grid using the gas solution.
- One-way coupling is acceptable for the MVP unless later approved otherwise.
  - Gas affects droplets.
  - Droplet feedback to gas may be neglected in the MVP.
- Tabulated area distributions may be interpolated between user points.
- The solver may use a marching or iterative approach, provided the chosen method and its stability limits are documented.
- The numerical method shall include checks for nonphysical states such as negative pressure, negative temperature, negative density, negative diameter, or invalid Mach number.

### 10.1 MVP Numerical Preference

The MVP should prefer:

- simple discretization,
- conservative input validation,
- bounded state updates,
- transparent model equations,
- reproducible outputs.

---

## 11. Validation Requirements

### 11.1 General Validation Strategy

Validation shall be defined explicitly as part of development. The MVP shall include a validation plan covering both solver sanity checks and physically expected trends.

### 11.2 Minimum Validation Cases

- Constant-area single-phase gas case with no droplets
- Smooth converging/diverging area-profile sanity case
- Droplet case with zero initial slip or near-zero slip
- Droplet case with increasing relative velocity that triggers breakup
- At least one steam case using the selected IF97-oriented property interface assumptions

### 11.3 Expected Validation Behaviors

- In a no-droplet case, the gas solver shall produce qualitatively correct quasi-1D compressible trends.
- If slip velocity is zero and remains zero, the breakup criterion shall not trigger.
- If relative velocity increases sufficiently, Weber number shall increase accordingly.
- When breakup is triggered, the droplet diameter metrics shall decrease according to the specified rule.
- Output units and sign conventions shall remain consistent across all validation cases.

### 11.4 Validation Artifacts

The project should eventually include:

- documented reference cases,
- expected trend descriptions,
- tolerances for regression testing,
- notes on limits of agreement for simplified models.

---

## 12. Error Handling Requirements

- The simulator shall validate required YAML fields before execution.
- The simulator shall reject unsupported working fluid names.
- The simulator shall reject invalid or nonphysical inputs such as:
  - nonpositive pressures,
  - nonpositive temperatures,
  - nonpositive diameters,
  - invalid axial grids,
  - invalid area values.
- The simulator shall report configuration errors with actionable messages.
- The simulator shall report numerical failure with location and state context when possible.
- The simulator shall avoid silent fallback behavior for ambiguous or unsupported inputs.
- The simulator shall distinguish between:
  - input validation errors,
  - model configuration errors,
  - numerical convergence/failure errors,
  - output writing errors.

---

## 13. Constraints

- Python only
- Intended to run in VS Code environments
- SI units only
- MVP implementation must stay focused on quasi-1D internal flow plus droplet transport plus simple breakup
- No implementation work shall begin before spec, architecture, tasks, and copilot instructions are approved in sequence
- The design shall separate:
  - physics,
  - solver,
  - IO,
  - plotting,
  - validation,
  - configuration
- Steam handling shall be designed for IF97 compatibility
- Numerical robustness shall be prioritized over feature breadth
- The first release shall favor maintainability and extension readiness over model complexity

---

## 14. Open Questions

### 14.1 Open Questions Requiring Later Decision

1. What exact steam property backend or library should be used for IF97 support?
2. Is steam support required in the first executable MVP, or is an IF97-ready interface sufficient while air is implemented first?
3. Should the quasi-1D gas solver for the MVP assume strictly isentropic core flow with boundary-condition closure, or a more general formulation with losses?
4. Should frictional losses be excluded entirely in the MVP?
5. What droplet loading range is expected, and is one-way coupling acceptable for all intended MVP use cases?
6. Is `water_mass_flow_rate` mandatory, or can droplet injection be specified by an alternative loading parameter?
7. What exact rule should be used after breakup to update mean and maximum droplet diameters?
8. Should evaporation be excluded entirely from the first executable MVP, even though future hooks may exist in the architecture?
9. What minimum validation references are acceptable for steam cases in the absence of experimental breakup data?
10. Should choking and supersonic branch handling be mandatory in MVP, or allowed only if needed by approved cases?

### 14.2 Working Assumptions Until Resolved

Unless later changed during architecture and task planning, the following assumptions are used for this specification:

- The MVP uses one-way coupling from gas to droplets.
- The MVP uses a simple spherical droplet drag model.
- The MVP uses a Weber-threshold breakup rule with user-configurable parameters.
- The MVP includes plotting and file export but not a GUI.
- The MVP uses equilibrium steam assumptions only.
- The MVP focuses on internal duct/nozzle flow only.

---

## 15. Acceptance Criteria

The specification will be considered satisfied for MVP planning when the future implementation can demonstrate all of the following:

### 15.1 Product Acceptance Criteria

- [ ] A user can define a simulation case in YAML.
- [ ] A user can specify air or steam as the working fluid.
- [ ] A user can provide inlet total pressure, inlet total temperature, outlet static pressure, and optional inlet wetness.
- [ ] A user can provide area distribution $A(x)$ and droplet injection conditions.
- [ ] The simulator computes axial results for pressure, temperature, working fluid velocity, Mach number, droplet velocity, droplet mean diameter, droplet maximum diameter, and Weber number.
- [ ] The simulator applies a simple breakup criterion based on Weber number threshold.
- [ ] The simulator exports results to CSV and JSON.
- [ ] The simulator generates plots of major variables versus $x$.
- [ ] The simulator runs from a CLI in Python.

### 15.2 Engineering Acceptance Criteria

- [ ] The software structure clearly separates physics, solver, IO, plotting, validation, and configuration layers.
- [ ] Assumptions and limitations are explicitly documented.
- [ ] Invalid inputs are rejected with clear errors.
- [ ] Numerical failures are surfaced clearly rather than silently ignored.
- [ ] At least the minimum validation behaviors defined in this specification are covered by planned tests or validation cases.

### 15.3 MVP Boundary Acceptance Criteria

- [ ] The MVP does not attempt to solve 3D CFD.
- [ ] The MVP does not include droplet-droplet collision or coalescence.
- [ ] The MVP does not include wall-film physics.
- [ ] The MVP does not include detailed external free jet physics.
- [ ] The MVP does not include plate impingement.
- [ ] The MVP does not include non-equilibrium condensation.
- [ ] The MVP does not include high-fidelity turbulence modeling.

---

## Appendix A. MVP Summary

### Included in MVP

- quasi-1D gas solver
- droplet transport with slip velocity
- simple Weber-threshold breakup
- YAML input file
- CLI execution
- CSV/JSON outputs
- Matplotlib plotting

### Not Included in MVP

- 3D CFD
- droplet-droplet collision/coalescence
- wall-film physics
- detailed free jet external field
- plate impingement
- non-equilibrium condensation
- high-fidelity turbulence modeling
