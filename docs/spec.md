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

## 1.1 Release Structure

This documentation set separates the project into three layers of scope:

- Core MVP: CLI-driven YAML input, quasi-1D solver execution, CSV/JSON export, and Matplotlib plotting.
- GUI extension: a later browser-based application layer built on the existing application-service boundary.
- Later advanced study features: non-MVP additions such as richer validation tooling or broader comparison workflows, only if separately approved.

The Core MVP remains CLI-focused and does not depend on a GUI.

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

- [x] The simulator shall accept case configuration from a YAML input file.
- [x] The simulator shall accept user-defined area distribution $A(x)$.
- [x] The simulator shall accept inlet total pressure.
- [x] The simulator shall accept inlet total temperature.
- [x] The simulator shall accept outlet static pressure.
- [x] The simulator shall accept working fluid selection as air or steam.
- [x] The simulator shall accept optional inlet wetness for steam cases.
- [x] The simulator shall accept droplet injection conditions.

### 5.2 Flow Simulation

- [x] The simulator shall solve a steady quasi-1D compressible flow problem along the axial coordinate.
- [x] The simulator shall compute axial distributions of pressure, temperature, density, velocity, and Mach number.
- [x] For supported converging-diverging Laval nozzle geometries, the simulator shall support choking-aware branch selection between subsonic and supersonic internal solutions.
- [x] For supported converging-diverging Laval nozzle geometries, the simulator shall support one internal normal shock located within the nozzle diverging section when required by outlet static pressure.
- [x] The simulator shall support a fluid property abstraction that allows air and steam implementations.
- [x] The steam implementation shall be designed to support IF97-based properties.
- [x] The first release shall assume equilibrium steam behavior.
- [x] The simulator shall support a shock-aware quasi-1D sampling refinement mode for supported internal-normal-shock Laval-nozzle solutions.
- [x] The simulator shall use a higher-accuracy safeguarded inversion of the area-Mach relation near $M=1$ and at high area ratios.
- [x] The simulator shall support explicit selection of an IF97 steam backend when the corresponding provider dependency is available.
- [x] The simulator shall support an operator-split two-way coupled mode that applies liquid-to-gas mass/momentum/energy source terms iteratively.
- [x] The simulator shall expose bounded convergence control for the two-way coupled loop and report coupling iteration diagnostics.

### 5.3 Droplet Simulation

- [x] The simulator shall compute droplet velocity evolution along $x$.
- [x] The simulator shall compute droplet mean diameter evolution along $x$.
- [x] The simulator shall compute droplet maximum diameter evolution along $x$.
- [x] The simulator shall compute slip velocity between working fluid and droplets.
- [x] The simulator shall compute droplet Weber number along $x$.
- [x] The simulator shall apply a simple breakup criterion when Weber number exceeds a defined threshold.
- [x] The simulator shall update droplet diameter metrics after breakup events according to the selected MVP breakup rule.
- [x] The simulator shall support configuration-driven coupling-mode selection between `one_way` (legacy MVP) and `two_way_approx` (reduced-order iterative feedback).
- [x] The simulator shall support selection of the KH-RT (Kelvin-Helmholtz / Rayleigh-Taylor) primary breakup model as an alternative to the Weber-threshold model.
- [x] The simulator shall support selection of the bag-stripping regime model as an alternative secondary breakup model.
- [x] When the KH-RT model is selected, child droplet diameter shall be derived from KH wavelength and RT stability criteria using liquid droplet properties.
- [x] When the bag-stripping model is selected, child diameter shall be computed as the stable Weber-number equilibrium diameter.
- [x] The simulator shall support a high-accuracy spherical drag correlation with low-, intermediate-, and high-Reynolds-number coverage.
- [x] The simulator shall support a non-spherical drag response option using user-configured droplet sphericity.
- [x] The simulator shall carry thermo-provider gas dynamic viscosity into droplet Reynolds-number and drag-response updates when available.
- [x] When the bag-stripping model is selected, child diameter shall be computed as the stable Weber-number equilibrium diameter.
- [x] The simulator shall expose local droplet-to-gas coupling source terms from the droplet transport layer for use by the gas solver.
- [x] The simulator shall support a probabilistic droplet-size state extension with at least standard deviation and Sauter mean diameter (SMD) in addition to mean/max diameters.
- [x] The simulator shall support configuration-driven selection between monodisperse and lognormal-moment droplet distribution representations.

### 5.4 Outputs

- [x] The simulator shall export numerical results to CSV.
- [x] The simulator shall export numerical results to JSON.
- [x] The simulator shall generate plots of major quantities versus $x$ using Matplotlib.
- [x] The simulator shall provide run status and error information through the CLI.

### 5.5 Software Structure

- [x] The software shall be structured to separate physics, solver, IO, plotting, validation, and configuration concerns.
- [x] The software shall be written in Python only.
- [x] The software shall be organized for testability and future extension.

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
| `coupling_mode` | Gas-droplet coupling mode selector | - | `one_way` or `two_way_approx` |
| `two_way_max_iterations` | Max outer iterations for reduced-order two-way mode | - | Positive integer |
| `two_way_feedback_relaxation` | Feedback relaxation coefficient for reduced-order two-way mode | - | Positive scalar |
| `two_way_convergence_tolerance` | Convergence tolerance for coupled iteration loop | - | Positive scalar |
| `droplet_density` | Representative droplet material density | kg/m³ | Default water-like value |
| `droplet_sphericity` | Non-spherical drag correction input | - | 1.0 = sphere; required for non-spherical drag option |
| `gas_solver_mode` | Quasi-1D gas solver mode selector | - | `baseline` or `shock_refined` |
| `droplet_distribution_model` | Droplet-size distribution state selector | - | `mono` or `lognormal_moments` |
| `droplet_distribution_sigma` | Lognormal spread parameter for droplet-size moments | - | Positive scalar, used when `lognormal_moments` |
| `khrt_B0` | KH child-radius proportionality constant | - | Default 0.61 (Beale & Reitz 1999) |
| `khrt_B1` | KH breakup time constant | - | Default 40.0 (dimensionless, range 10–60) |
| `khrt_Crt` | RT instability constant | - | Default 0.1 (range 0.1–0.5) |
| `liquid_density` | Representative droplet liquid density | kg/m³ | Default 998.2 (water at ~20 °C) |
| `liquid_viscosity` | Representative droplet liquid dynamic viscosity | Pa·s | Default 1.002 × 10⁻³ (water at ~20 °C) |

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
- `surface_tension`
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
- slip velocity
- surface tension
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
- An optional IF97 backend may be used for vapor-region states when the dependency is installed and the requested case remains within the supported pressure-temperature envelope.

### 9.3 Droplet Assumptions

- Droplets are water droplets.
- Droplets are represented by one or more bulk/representative quantities rather than a full population balance.
- Droplet transport is evaluated along the same axial coordinate as the gas solution.
- Droplet acceleration is driven primarily by aerodynamic drag and slip velocity.
- Droplet shape deformation is not resolved explicitly in the MVP.

### 9.4 Breakup Assumptions

- Breakup is represented by a pluggable, configuration-driven model.
- The default model uses a Weber-number threshold: when $We > We_{crit}$, droplet diameter metrics are reduced by a prescribed factor.
- The KH-RT model derives child droplet diameter from Kelvin-Helmholtz surface stripping and Rayleigh-Taylor bulk breakup wavelengths using the Reitz (1987) curve-fit. Child diameter is taken as the minimum of the KH and RT equilibrium sizes when each applies.
- The bag-stripping model computes the stable Weber-equilibrium child diameter: $d_s = We_{crit} \cdot \sigma / (\rho_g \cdot u_{rel}^2)$, where $u_{rel}$ is the local slip velocity. This targets the diameter at which breakup would just cease.
- All breakup models share the same stateless, cell-local interface and return a structured `BreakupDecision`.
- Breakup time-scale physics and deformation history are not tracked in the quasi-1D MVP framework.

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

Approved post-MVP refinements may include:

- shock-aware local axial refinement around a fitted internal normal shock,
- safeguarded Newton-bisection area-Mach inversion,
- improved drag correlations with non-spherical corrections,
- more precise steam property backends behind the thermo abstraction.

For coupled gas-droplet source-term iterations:

- the loop shall remain bounded by configured max-iteration and convergence-tolerance guards,
- source-term corrections shall be relaxation-controlled to avoid nonphysical gas-state updates,
- diagnostics shall indicate when the coupled loop converged or terminated by iteration cap.

---

## 11. Validation Requirements

### 11.1 General Validation Strategy

Validation shall be defined explicitly as part of development. The MVP shall include a validation plan covering both solver sanity checks and physically expected trends.

### 11.2 Minimum Validation Cases

- Constant-area single-phase gas case with no droplets
- Smooth converging/diverging area-profile sanity case
- Laval-nozzle internal-flow case spanning subsonic, internal-normal-shock, exit-shock-limit, and fully supersonic internal solution families under varying back pressure
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

### 11.5 Quantitative Validation and Sensitivity (Mandatory)

- [x] The simulator shall support a quantitative validation-campaign report that compares selected output metrics against reference targets from documented validation cases.
- [x] The simulator shall support one-at-a-time sensitivity analysis for selected model parameters and report normalized sensitivity coefficients.
- [x] The simulator shall support bounded parameter optimization over user-provided candidate sets and report the best objective score with associated parameters.
- [x] The simulator shall support uncertainty summary statistics (mean, standard deviation, 95% confidence interval) for objective values derived from validation samples.

### 11.6 Recommended Execution Order

The recommended workflow for validation-driven improvement shall be:

1. execute baseline validation campaign on documented cases,
2. run sensitivity analysis to rank high-impact parameters,
3. run bounded optimization on top-ranked parameters,
4. run uncertainty aggregation for the optimized candidate,
5. compare baseline vs optimized objective and record findings.

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
   - **Resolved (MVP):** The MVP uses a restricted equilibrium-vapor approximation (`SteamThermoProvider`) as an IF97-ready placeholder. The thermo interface is designed for clean future replacement by a full IF97 library.
2. Is steam support required in the first executable MVP, or is an IF97-ready interface sufficient while air is implemented first?
   - **Resolved:** Both air and steam are executable in the MVP. Steam uses an idealized vapor model behind the shared `ThermoProvider` interface.
3. Should the quasi-1D gas solver for the MVP assume strictly isentropic core flow with boundary-condition closure, or a more general formulation with losses?
   - **Resolved:** The MVP uses strictly isentropic quasi-1D flow with area-Mach closure. No loss models.
4. Should frictional losses be excluded entirely in the MVP?
   - **Resolved:** Yes, frictional losses are excluded.
5. What droplet loading range is expected, and is one-way coupling acceptable for all intended MVP use cases?
   - **Resolved:** One-way coupling (gas → droplets) is used. Droplet feedback to gas is neglected.
6. Is `water_mass_flow_rate` mandatory, or can droplet injection be specified by an alternative loading parameter?
   - **Resolved:** `water_mass_flow_rate` is optional. Droplet injection is specified by initial velocity, mean diameter, and maximum diameter.
7. What exact rule should be used after breakup to update mean and maximum droplet diameters?
   - **Resolved:** When $We > We_{crit}$: `d_mean_new = d_mean × breakup_factor_mean`, `d_max_new = max(d_max × breakup_factor_max, d_mean_new)`. Both factors are required user inputs in $(0, 1)$.
8. Should evaporation be excluded entirely from the first executable MVP, even though future hooks may exist in the architecture?
   - **Resolved:** Yes, evaporation is excluded from the MVP.
9. What minimum validation references are acceptable for steam cases in the absence of experimental breakup data?
   - **Resolved:** Trend-based validation is used: gas-solution completeness, slip-driven acceleration, breakup threshold behavior. No experimental reference data required for MVP.
10. Should choking and supersonic branch handling be mandatory in MVP, or allowed only if needed by approved cases?
   - **Resolved:** Choking-aware branch selection is implemented for supported converging-diverging Laval nozzle geometries. The runtime gas solver supports subsonic internal solutions, fully supersonic internal solutions, and one fitted internal normal shock in the diverging section. Downstream external-jet shock cells, oblique shocks, and expansion fans remain out of scope.

### 14.2 Working Assumptions Until Resolved

Unless later changed during architecture and task planning, the following assumptions are used for this specification:

- The MVP uses one-way coupling from gas to droplets.
- The MVP uses a simple spherical droplet drag model.
- The MVP uses a Weber-threshold breakup rule with user-configurable parameters.
- The MVP includes plotting and file export but not a GUI.
- The MVP uses equilibrium steam assumptions only.
- The MVP focuses on internal duct/nozzle flow only.

---


### 15. Acceptance Criteria

The specification will be considered satisfied for MVP planning when the future implementation can demonstrate all of the following:

### 15.1 Product Acceptance Criteria

- [x] A user can define a simulation case in YAML.
- [x] A user can specify air or steam as the working fluid.
- [x] A user can provide inlet total pressure, inlet total temperature, outlet static pressure, and optional inlet wetness.
- [x] A user can provide area distribution $A(x)$ and droplet injection conditions.
- [x] The simulator computes axial results for pressure, temperature, working fluid velocity, Mach number, droplet velocity, droplet mean diameter, droplet maximum diameter, and Weber number.
- [x] The simulator applies a simple breakup criterion based on Weber number threshold.
- [x] The simulator exports results to CSV and JSON.
- [x] The simulator generates plots of major variables versus $x$.
- [x] The simulator runs from a CLI in Python.

---

## Appendix C. Laval Nozzle Back-Pressure Sweep and Validation (Phase 26)

### C.1 Purpose

To support robust validation of the quasi-1D solver for converging-diverging Laval nozzles, the simulator shall provide:

- A CLI-accessible command to run a back-pressure sweep utility, generating a family of internal-flow solutions for a fixed nozzle geometry and varying outlet static pressure.
- Automated generation of $p/p_0$ (static-to-total pressure) validation plots and summary reports for the sweep outputs, suitable for comparison to textbook trends.

### C.2 CLI Sweep Command Requirements

- The CLI shall provide a command (e.g., `supersonic-atomizer sweep --case <yaml> --out <dir> [--back-pressures ...]`) to run a sweep over a user-specified set or range of outlet static pressures for a given Laval nozzle case definition.
- The sweep utility shall:
   - Accept a YAML case file as the base geometry and inlet condition definition.
   - Accept a list or range of outlet static pressures to sweep.
   - For each back pressure, run the simulation and collect results.
   - Write all results to a sweep output directory, with clear labeling of each run.
   - Aggregate results for post-processing and validation.

### C.3 Automated Validation Report Requirements

- After running the sweep, the utility shall:
   - Generate a summary CSV and JSON of all runs, including key fields (e.g., $x$, $p$, $p/p_0$, Mach number, shock location if present).
   - Produce a validation plot of $x$ vs $p/p_0$ for all sweep cases, with regime labels (subsonic, supersonic, shock-internal, etc.).
   - Optionally generate a report (Markdown or HTML) summarizing the sweep, validation trends, and any detected anomalies.

### C.4 Constraints and Scope

- The sweep and validation report features must not break the existing single-case CLI or GUI workflows.
- All outputs must be SI-unit-consistent and reproducible.
- The sweep utility must use only documented and supported solver/model interfaces.
- The validation logic must be modular and testable.

### C.5 Acceptance Criteria

- [x] A user can invoke the sweep utility from the CLI with a YAML case and a set/range of back pressures.
- [x] The utility generates labeled output directories/files for each run.
- [x] The utility produces a combined $x$ vs $p/p_0$ plot and summary CSV/JSON for all sweep cases.
- [x] The utility generates a validation report summarizing regime coverage and qualitative agreement with expected trends.
- [x] All outputs are compatible with downstream analysis and regression testing.

### 15.2 Engineering Acceptance Criteria

- [x] The software structure clearly separates physics, solver, IO, plotting, validation, and configuration layers.
- [x] Assumptions and limitations are explicitly documented.
- [x] Invalid inputs are rejected with clear errors.
- [x] Numerical failures are surfaced clearly rather than silently ignored.
- [x] At least the minimum validation behaviors defined in this specification are covered by planned tests or validation cases.

### 15.3 MVP Boundary Acceptance Criteria

- [x] The MVP does not attempt to solve 3D CFD.
- [x] The MVP does not include droplet-droplet collision or coalescence.
- [x] The MVP does not include wall-film physics.
- [x] The MVP does not include detailed external free jet physics.
- [x] The MVP does not include plate impingement.
- [x] The MVP does not include non-equilibrium condensation.
- [x] The MVP does not include high-fidelity turbulence modeling.

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

---

## Appendix B. GUI Extension — Scope and Requirements

> This appendix defines the scope and functional requirements for the interactive GUI layer planned beyond the CLI-only MVP.
> The CLI engine and all physics remain unchanged. The GUI is a front-end wrapper only.

### B.1 Purpose

The GUI extension provides a browser-based interactive interface for the simulator, enabling case management, condition setup, solver execution monitoring, and result visualization without requiring CLI or YAML knowledge from the user.

### B.2 Layout Overview

```
┌──────────────────┬───────────────────────────────────────────────────┐
│  Left Panel      │  Main Area                                        │
│  (fixed)         │                                                   │
│                  │  ┌─[ Pre ]───────────────────────────────────┐   │
│  Case list       │  │  Tab1: Analysis Conditions                │   │
│  ─────────       │  │  Tab2: Grid Definition                    │   │
│  ○ case_001     │  └───────────────────────────────────────────┘   │
│  ○ case_002     │                                                   │
│  ● case_003     │  ┌─[ Solve ]─────────────────────────────────┐   │
│                  │  │  Run / Status / Completion / Diagnostics  │   │
│  [+ New Case]    │  │  Polling / Result Ready                    │   │
│  [Open Case]     │  └───────────────────────────────────────────┘   │
│                  │                                                   │
│                  │  ┌─[ Post ]──────────────────────────────────┐   │
│                  │  │  Tab1: Graphs                             │   │
│                  │  │  Tab2: Results Table                      │   │
│                  │  └───────────────────────────────────────────┘   │
└──────────────────┴───────────────────────────────────────────────────┘
```

### B.3 Left Panel — Case Management

- [ ] The GUI shall display a list of all saved simulation cases.
- [ ] The user shall be able to create a new case with a unique name.
- [ ] The user shall be able to open (load) an existing case and restore its conditions.
- [ ] The currently active case shall be visually highlighted.
- [ ] Case state shall persist across sessions using a local YAML-backed case store.

### B.4 Pre Tab 1 — Analysis Conditions

The user shall be able to set all required simulation inputs through form controls:

- [ ] Working fluid selection: `air` or `steam`.
- [ ] Inlet total temperature $T_0$ (K).
- [ ] Inlet total pressure $P_0$ (Pa).
- [ ] Outlet static pressure $P_2$ (Pa).
- [ ] Droplet injection conditions: initial velocity, mean diameter, maximum diameter.
- [ ] Breakup model parameters: critical Weber number, breakup factor mean, breakup factor max.
- [ ] Optional: inlet wetness (steam cases only).
- [ ] Numeric condition fields shall accept either a single SI value or multiple SI values entered as comma-, space-, semicolon-, or newline-separated tokens.
- [ ] Multi-value numeric entries in the Conditions UI shall define a GUI-side parameter sweep for Solve-tab execution and shall not require separate case files.
- [ ] Input validation shall be performed before the Solve tab becomes active.
- [ ] All fields shall display SI unit labels.

### B.5 Pre Tab 2 — Grid Definition

- [ ] The user shall be able to define the axial domain extents ($x_{start}$, $x_{end}$) and cell count.
- [ ] The user shall be able to enter a tabulated area distribution $(x, A)$ as an editable table.
- [ ] The GUI shall display a preview plot of the area profile $A(x)$.
- [ ] The GUI shall reject nonpositive area values with an inline error message.

### B.6 Solve Tab — Solver Execution

> **MVP note:** The quasi-1D solver uses a spatial marching method, not an iterative convergence loop. The MVP GUI therefore exposes run control, status, completion outcome, diagnostics, and user-readable errors rather than iteration-based convergence controls.

- [ ] The GUI shall provide a **Run** button that invokes the simulation engine.
- [ ] The GUI shall display solver progress or status during execution.
- [ ] The GUI shall display a run-progress indicator showing whether a run is in progress or complete.
- [ ] The GUI shall report solver completion status: success, validation outcome, and output location.
- [ ] The GUI shall report solver errors in a user-readable format.
- [ ] The Run button shall be disabled while a simulation is in progress.
- [ ] When one or more numeric condition fields contain multiple values, the Solve tab shall expand those values into a parameter sweep over the Cartesian product of the entered value lists.
- [ ] The Solve tab shall validate multi-value numeric tokens before the run starts and shall reject malformed tokens or excessive sweep sizes with a user-readable error.
- [ ] Each expanded run shall use an immutable copy-on-run payload so later UI edits do not affect in-flight runs.
- [ ] Solve status shall summarize the number of expanded runs executed for the current sweep.

### B.7 Post Tab 1 — Graphs

- [ ] The GUI shall display axial profile plots for all required MVP output quantities:
  - pressure, temperature, working fluid velocity, droplet velocity,
   - slip velocity, surface tension,
   - Mach number, droplet mean diameter, droplet maximum diameter, Weber number.
- [ ] The user shall be able to select which quantities to display.
- [ ] The plots shall update automatically after each completed run.
- [ ] The user shall be able to export displayed plots as PNG files.
- [ ] When Solve executes multiple expanded runs, the Graphs tab shall overlay those runs on the same axes with a legend derived from the varied parameter values.

### B.8 Post Tab 2 — Results Table

- [ ] The GUI shall display a tabular view of all axial result fields.
- [ ] The table shall be scrollable and show all $x$ positions.
- [ ] The user shall be able to export the results table as CSV.
- [ ] When Solve executes multiple expanded runs, the results table shall aggregate all runs and include a run-label column identifying the varied parameter combination for each row.

### B.9 GUI Constraints

- The GUI must not contain solver, physics, or config-parsing logic.
- The GUI must invoke the existing application service boundary unchanged.
- All computation remains in the existing Python solver engine.
- The GUI layer must be replaceable without touching solver code.
- The GUI must remain consistent with the local YAML-backed case store representation internally.
- When a run starts, the GUI snapshots the current case state into an immutable run payload; later case edits do not affect the running job.
- Technology selection is deferred to architecture planning.
- Multi-value parsing and parameter-sweep expansion must remain in the GUI/application orchestration layer; the solver engine itself must continue to receive one single-case payload per run.
- Multi-value text entered in the Conditions UI must remain session-local until Solve expands it; the case store must continue to persist solver-compatible single-case YAML.

### B.10 GUI Out of Scope

- 3D visualization
- Multi-case comparison view (out of scope for the MVP GUI; may be considered later)
- Live/streaming solver output during execution
- User authentication or multi-user support
- Mobile layout

> Same-case parameter sweeps initiated from multi-value numeric entries in the Conditions UI are in scope. A dedicated general-purpose multi-case comparison workspace remains out of scope.

### B.11 Unit Settings

The GUI shall provide a configurable settings page for display units. All solver inputs and outputs remain in SI units internally; unit selection affects only what is displayed in the Post tabs.

**Default display units and supported alternatives:**

| Quantity group | Default | Alternatives |
|---|---|---|
| Pressure | kPa | Pa, MPa, bar |
| Temperature | K | \u00b0C |
| Velocity | m/s | \u2014 |
| Droplet diameter | \u03bcm | m, mm, nm |
| Axial position ($x$) | m | mm, cm |
| Cross-section area | m\u00b2 | mm\u00b2, cm\u00b2 |
| Density | kg/m\u00b3 | \u2014 |

**Requirements:**

- [ ] The GUI shall provide a settings page where the user can select display units for each quantity group.
- [ ] Unit selection shall affect only display outputs (Post tab plots and results table).
- [ ] All solver inputs and internal computations shall remain in SI units.
- [ ] Pre-tab condition inputs shall be labeled and accepted in SI units only.
- [ ] Display unit preferences shall persist within the current browser session.
- [ ] The results table CSV export shall label column headers with the selected display unit (e.g. `pressure [kPa]`).
- [ ] The unit settings page shall show the currently selected unit for each group and allow changes.
