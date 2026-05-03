# Supersonic Atomizer Simulator Architecture

## 1. System Overview

This document defines the target architecture for the Python-based quasi-1D droplet atomization simulator described in [docs/spec.md](docs/spec.md).

The system is a research-oriented engineering application that reads a YAML case definition, builds a one-dimensional computational representation of a duct or nozzle, solves a steady quasi-1D compressible working-fluid problem, evaluates droplet transport and simple breakup along the axial direction, and writes numerical and plotted outputs.

The architecture is designed around the following core goals:

- modularity,
- numerical robustness,
- explicit model boundaries,
- clean replacement of thermo backends,
- pluggable breakup models,
- testability and validation support,
- readiness for future steam IF97 integration and later model growth.

At the highest level, the application flow is:

1. CLI receives a case path and run options.
2. Configuration layer loads and validates YAML input.
3. Geometry and grid layers construct the computational axis and area profile.
4. Thermodynamic layer instantiates the selected working-fluid property provider.
5. Gas solver computes quasi-1D axial gas states.
6. Droplet solver advances droplet state using gas-state inputs.
7. Breakup model evaluates breakup criteria and updates droplet size metrics.
8. Result assembly layer produces structured outputs.
9. IO and plotting layers write files and figures.
10. Validation hooks and run summaries report quality and failure information.

---

## 2. Design Principles

### 2.1 Separation of Concerns

Each major concern shall live in an isolated module group:

- configuration parsing and validation,
- domain data models,
- thermo/property evaluation,
- geometry and area representation,
- grid generation,
- gas solving,
- droplet solving,
- breakup logic,
- result serialization,
- plotting,
- validation,
- CLI orchestration.

### 2.2 Interface-Driven Design

The solver core shall depend on stable interfaces rather than concrete implementations. This is especially important for:

- working-fluid property backends,
- breakup models,
- drag models,
- future validation/reference providers.

### 2.3 Explicit Data Contracts

Key solver inputs and outputs shall be represented using typed data models rather than loose dictionaries wherever practical. This reduces ambiguity and improves testability.

### 2.4 MVP Simplicity

The architecture shall support future growth, but the initial design shall not overcomplicate the MVP. The first implementation should remain focused on:

- quasi-1D internal flow,
- representative droplet transport,
- simple Weber-threshold breakup,
- YAML to results pipeline.

### 2.5 Replaceable Physics Components

The architecture shall make it possible to replace or add:

- steam property implementations,
- breakup models,
- drag correlations,
- gas solver formulations,
without rewriting the full application workflow.

### 2.6 Robust Failure Handling

Input, model-selection, and numerical errors shall be surfaced explicitly and close to their source.

---

## 3. Module Decomposition

### 3.1 CLI Layer

Responsibilities:

- parse command-line arguments,
- locate input case files,
- invoke simulation runs,
- report progress and summarized errors,
- optionally select output directory and run mode.

The CLI shall not contain physics or solver logic.

### 3.2 Config Layer

Responsibilities:

- load YAML input,
- validate required fields,
- normalize units and defaults,
- map raw config into typed case-definition objects.

This layer is the only layer that should directly interpret raw external configuration structure.

### 3.3 Domain Model Layer

Responsibilities:

- define core data structures used across the application,
- represent states, parameters, geometry definitions, solver outputs, and diagnostics,
- enforce semantic clarity between user input, internal states, and output summaries.

This layer contains no file IO and no numerical solving.

### 3.4 Thermo Layer

Responsibilities:

- expose working-fluid property interfaces,
- provide concrete air and steam property providers,
- isolate all property calculations from the gas solver.

The steam implementation shall be swappable so IF97 support can be introduced or replaced cleanly.

The thermo selection boundary shall allow multiple named steam providers, including the existing equilibrium approximation and an optional IF97-backed vapor-region provider.

### 3.5 Geometry Layer

Responsibilities:

- represent the axial geometry domain,
- represent area distribution $A(x)$,
- provide interpolation of tabulated area data,
- provide geometric queries required by the gas solver.

### 3.6 Grid Layer

Responsibilities:

- generate the axial computational grid,
- store grid spacing and node locations,
- provide utility operations for marching and plotting.

### 3.7 Gas Solver Layer

Responsibilities:

- solve steady quasi-1D gas flow along the axial grid,
- compute gas pressure, temperature, density, velocity, and Mach number,
- select the appropriate internal branch for supported converging-diverging Laval nozzles (subsonic, choked/supersonic, or one internal normal-shock-fitted branch),
- support shock-aware local sampling refinement around a fitted internal normal shock without changing the user-configured base grid,
- use safeguarded root-finding for area-Mach inversion near singular regions,
- support optional liquid-to-gas coupling source-term application (mass/momentum/energy) on assembled gas states,
- use thermo-provider interfaces rather than direct property formulas where possible,
- surface numerical diagnostics and failure conditions.

### 3.8 Droplet Solver Layer

Responsibilities:

- initialize droplet state from case inputs,
- compute slip velocity relative to gas,
- compute drag-driven droplet acceleration,
- select and evaluate a configured drag correlation,
- support non-spherical drag correction parameters through the drag-model boundary,
- update droplet velocity and size metrics along the grid,
- expose local coupling-source summaries required by two-way gas feedback,
- maintain optional probabilistic droplet-size moments (e.g., diameter standard deviation and SMD),
- request breakup decisions from the breakup module.

Additional responsibility: Injection-mode handling

- The Droplet Solver layer shall support two injection modes selected via configuration: `droplet_injection` and `liquid_jet_injection`.
- `droplet_injection` provides initial droplet parcels directly from case inputs and requires no primary-atomization logic in the solver.
- `liquid_jet_injection` supplies liquid-jet properties; the architecture shall include a lightweight primary-breakup coordinator that:
  - computes `L_primary_breakup` from a configurable correlation (uses We_g, Oh_l, Re_l, q, and density ratio as inputs),
  - for x < L_primary_breakup treats the liquid as an intact core (no droplet parcels),
  - at x >= L_primary_breakup generates initial droplet parcels using a selectable `initial_SMD_model` and then invokes the standard droplet transport and breakup pipeline.
- The primary-breakup coordinator must be a small, testable component in the droplet layer (for example `solvers/droplet/primary_breakup.py`) that returns the primary-breakup length and generated SMD parameters and does not perform Lagrangian droplet transport itself.

Integration notes:

- The `primary_breakup` module shall be parameterized by a `primary_breakup_coefficient` to allow tuning and to remain empirical at first implementation.
- The Droplet Solver shall accept optional `liquid_*` inputs in `DropletInjectionConfig` or a new `LiquidJetConfig` domain model; translation and defaults should be handled in the config layer.
- The GUI and config translator must expose `injection_mode` and the relevant input fields for the selected mode only.


Drag models shall remain isolated in `solvers/droplet/drag_models.py` and must not embed breakup logic or read raw configuration.

Coupling-source extraction shall remain isolated in `solvers/droplet/transport_solver.py` and must not directly mutate gas-side state.

### 3.9 Breakup Model Layer

Responsibilities:

- define the breakup interface (`BreakupModel` / `BreakupModelInputs`),
- implement concrete breakup models behind that interface,
- return structured `BreakupDecision` objects with updated diameter metrics and diagnostics,
- keep model selection configuration-driven via the registry,
- allow later replacement or addition of models without touching the solver core.

This layer shall remain fully pluggable.

#### Registered breakup models

| Config name | Module | Physics basis |
|---|---|---|
| `weber_critical` | `breakup/weber_critical.py` | Weber-number threshold + prescribed reduction factors (MVP default) |
| `khrt` | `breakup/khrt.py` | KH instability (Reitz 1987 curve-fit) + RT bulk breakup; child diameter from wavelength physics |
| `bag_stripping` | `breakup/bag_stripping.py` | Stable Weber equilibrium diameter; child = $We_{crit} \cdot \sigma / (\rho_g u_{rel}^2)$ |

#### Model boundary rules

- Breakup models must not read YAML directly.
- Breakup models must not call the gas or droplet solver.
- All liquid property assumptions (density, viscosity, surface tension) used by breakup models must come from model parameters, not be hard-wired silently.
- Weber number must be computed and stored in every `BreakupDecision` regardless of model.
- The `diagnostics` validator must remain compatible with all registered models.

### 3.10 IO Layer

Responsibilities:

- write CSV outputs,
- write JSON outputs,
- serialize run metadata,
- organize output directories and filenames.

### 3.11 Plotting Layer

Responsibilities:

- generate Matplotlib plots from structured results,
- keep figure-generation logic separate from solver logic,
- support consistent plot styling and naming.

### 3.12 Validation Layer

Responsibilities:

- run predefined sanity checks,
- compare selected outputs against expected trends or references,
- compute objective-error metrics for validation campaigns,
- run sensitivity analysis over bounded parameter perturbations,
- run bounded candidate optimization and uncertainty aggregation,
- support regression-test case definitions,
- report validation summaries independent of CLI formatting.

### 3.13 Application Orchestration Layer

Responsibilities:

- coordinate config loading,
- instantiate geometry, thermo, and model providers,
- run gas and droplet solvers in sequence,
- run optional operator-split two-way coupled iterations by alternating gas solve / droplet solve / source-term correction,
- collect results,
- invoke output writing and plotting,
- produce run summary objects.

This layer is the main application workflow boundary.

---

## 4. Data Flow

### 4.1 High-Level Flow

The expected data flow is:

1. YAML file -> raw configuration
2. Raw configuration -> validated case definition
3. Case definition -> geometry definition + grid + selected model providers
4. Geometry + grid + thermo provider + boundary conditions -> gas solution
5. Gas solution + droplet injection data + drag model + breakup model -> droplet solution
6. Gas solution + droplet solution + metadata + diagnostics -> simulation result
7. Simulation result -> CSV/JSON writers and plotting
8. Simulation result + validation rules -> validation report

### 4.2 Flow Ownership

To keep boundaries clean:

- config owns external representation,
- domain models own internal representation,
- solvers own state evolution,
- IO owns file serialization,
- plotting owns visual outputs,
- validation owns reference comparisons and quality checks.

### 4.3 Dependency Direction

Dependencies should generally point inward toward abstract interfaces:

- CLI depends on application services.
- Application services depend on config, domain, and solver interfaces.
- Solvers depend on domain models and abstract thermo/model interfaces.
- Concrete thermo and breakup implementations depend on domain contracts, not on CLI or IO.
- IO and plotting depend on result models only.

---

## 5. Key Data Models

The following data models are recommended architectural concepts. Names may evolve during implementation, but the separation should remain.

### 5.1 Case Configuration Models

- `CaseConfig`
  - validated full simulation configuration
- `FluidConfig`
  - working fluid selection and thermo settings
- `BoundaryConditionConfig`
  - inlet total pressure, inlet total temperature, outlet static pressure, optional wetness
- `GeometryConfig`
  - axial domain and area-distribution definition
- `DropletInjectionConfig`
  - initial droplet velocity and diameter conditions
- `ModelSelectionConfig`
  - drag model, breakup model, thermo backend selection, gas solver mode, coupling mode selection, optional parameters
- `OutputConfig`
  - output directory, file selections, plotting options

### 5.2 Geometry and Grid Models

- `AxialGrid`
  - node positions, spacing, extent
- `AreaProfile`
  - tabulated or analytic area representation
- `GeometryModel`
  - combined geometry metadata and query methods

### 5.3 Thermo and Fluid State Models

- `ThermoState`
  - pressure, temperature, density, enthalpy, sound speed, or other required properties
- `GasState`
  - axial gas state at one location
- `GasSolution`
  - full axial gas solution arrays and diagnostics

### 5.4 Droplet Models

- `DropletState`
  - droplet velocity, mean diameter, maximum diameter, Weber number, optional Reynolds number
- `DropletSolution`
  - full axial droplet history and breakup flags
- `BreakupDecision`
  - triggered or not, updated diameters, diagnostic values

### 5.5 Result and Diagnostics Models

- `SimulationResult`
  - combined gas and droplet solutions, case metadata, and output-ready arrays
- `RunDiagnostics`
  - warnings, convergence messages, failure context, numerical notes
- `ValidationReport`
  - pass/fail summary and validation observations

### 5.6 Error Models

- `InputParsingError`
- `ConfigurationError`
- `NumericalError`
- `ThermoError`
- `OutputError`
- `ValidationError`

These are implemented as concrete exception classes in `common/errors.py` and used across config, thermo, solver, IO, and validation boundaries.

---

## 6. Package/Directory Structure

A recommended project layout is:

```text
project/
  ├─ docs/
  │   ├─ spec.md
  │   ├─ architecture.md
  │   └─ tasks.md
  ├─ src/
  │   └─ supersonic_atomizer/
  │       ├─ app/
  │       │   ├─ run_simulation.py
  │       │   ├─ services.py
  │       │   └─ result_assembly.py
  │       ├─ cli/
  │       │   └─ main.py
  │       ├─ config/
  │       │   ├─ loader.py
  │       │   ├─ schema.py
  │       │   ├─ semantics.py
  │       │   ├─ defaults.py
  │       │   └─ translator.py
  │       ├─ domain/
  │       │   ├─ case_models.py
  │       │   ├─ state_models.py
  │       │   └─ result_models.py
  │       ├─ thermo/
  │       │   ├─ interfaces.py
  │       │   ├─ air.py
  │       │   ├─ steam.py
  │       │   ├─ selection.py
  │       │   └─ failures.py
  │       ├─ geometry/
  │       │   ├─ area_profile.py
  │       │   ├─ geometry_model.py
  │       │   └─ diagnostics.py
  │       ├─ grid/
  │       │   └─ axial_grid.py
  │       ├─ solvers/
  │       │   ├─ gas/
  │       │   │   ├─ quasi_1d_solver.py
  │       │   │   ├─ boundary_conditions.py
  │       │   │   ├─ state_updates.py
  │       │   │   └─ diagnostics.py
  │       │   └─ droplet/
  │       │       ├─ transport_solver.py
  │       │       ├─ drag_models.py
  │       │       ├─ updates.py
  │       │       └─ diagnostics.py
  │       ├─ breakup/
  │       │   ├─ interfaces.py
  │       │   ├─ weber_critical.py
  │       │   ├─ registry.py
  │       │   └─ diagnostics.py
  │       ├─ io/
  │       │   ├─ csv_writer.py
  │       │   ├─ json_writer.py
  │       │   └─ paths.py
  │       ├─ plotting/
  │       │   ├─ plot_profiles.py
  │       │   └─ styles.py
  │       ├─ validation/
  │       │   ├─ sanity_checks.py
  │       │   └─ reporting.py
  │       └─ common/
  │           └─ errors.py
  ├─ tests/
  ├─ examples/
  │   ├─ air_nozzle.yaml
  │   └─ steam_nozzle.yaml
  └─ README.md
```

This structure keeps domain and interface definitions separate from concrete implementations.

---

## 7. Solver Sequence

### 7.1 End-to-End Sequence

The application should execute in the following sequence:

1. Parse CLI arguments.
2. Load YAML file.
3. Validate config schema and semantic constraints.
4. Build case-definition models.
5. Build area profile and axial grid.
6. Select thermo backend based on fluid and model settings.
7. Select breakup model implementation.
8. Run gas solver, including choking-aware branch selection and optional internal normal-shock fitting for supported Laval-nozzle cases.
9. Initialize droplet state at inlet or injection location.
10. March droplet solution along the gas-state field.
11. At each step, compute slip-driven quantities and call breakup model as needed.
12. Assemble final simulation result.
13. Run post-solve validation and sanity checks.
14. Write CSV and JSON outputs.
15. Generate plots.
16. Return run summary and exit status.

### 7.2 Gas-to-Droplet Dependency

Default behavior remains one-way coupling (`one_way`): the droplet solver depends on the gas solution, but the gas solver does not depend on droplet feedback.

An optional reduced-order mode (`two_way_approx`) is supported in the application orchestration layer. In this mode, the workflow runs a short outer iteration loop that:

1. solves gas and droplet fields,
2. estimates feedback strength from mass loading and slip,
3. applies a bounded gas-side correction,
4. re-solves droplets on the corrected gas field.

This keeps the core gas solver boundary unchanged while enabling UI/CLI selection between legacy one-way and approximate two-way behavior.

### 7.3 Future Sequence Evolution

Later versions may allow:

- iterative gas-droplet coupling,
- multiple droplet populations,
- evaporation steps,
- stronger thermo-state coupling for steam/wetness effects.

The orchestration layer should be able to evolve without changing CLI or IO boundaries.

---

## 8. Interface Boundaries

### 8.1 Thermo Interface Boundary

The gas solver shall depend on a thermo-provider abstraction rather than directly on `air` or `steam` implementations.

The thermo interface should conceptually provide operations such as:

- evaluate state from required independent variables,
- compute density,
- compute sound speed,
- compute enthalpy or equivalent energy quantity,
- expose model metadata and validity limits.

This allows `steam_if97` to be introduced or replaced without changing solver orchestration.

### 8.2 Breakup Interface Boundary

The droplet solver shall call a breakup-model abstraction.

The breakup interface should conceptually accept:

- local gas state,
- local droplet state,
- model parameters,

and return:

- breakup decision,
- updated droplet metrics,
- diagnostics.

This allows Weber-threshold logic to be replaced later by TAB, KH-RT, or more advanced methods.

### 8.3 Geometry/Grid Boundary

The gas solver should not care whether area data came from a table or an analytic function. It should consume a geometry abstraction that can answer area queries consistently along the grid.

### 8.4 IO Boundary

Writers and plotters shall consume structured result objects only. They shall not reconstruct physics or redo solver calculations.

### 8.5 Validation Boundary

Validation should consume stable result models and case metadata, not raw solver internals. This allows validation tooling to remain compatible while solver implementations evolve.

---

## 9. Configuration Strategy

### 9.1 Configuration Source

The primary external configuration source is YAML.

### 9.2 Configuration Processing Stages

Configuration handling occurs in five stages:

1. raw YAML parse (`loader`)
2. schema validation — required sections and field presence (`schema`)
3. semantic validation — physical and structural constraints (`semantics`)
4. defaults application — centralized default injection (`defaults`)
5. translation into internal typed case models (`translator`)

This avoids leaking YAML structure into solver code.

### 9.3 Defaults Strategy

Defaults should be centralized in the config layer rather than embedded throughout the solver modules. This makes assumptions visible and auditable.

Examples of likely centralized defaults:

- default drag model,
- default breakup model,
- default critical Weber number,
- default output file selections,
- default plotting enablement.

### 9.4 Configuration Versioning

The architecture should allow a future configuration version field so schema evolution can occur without breaking older case files.

### 9.5 Open Questions / Assumptions

Current architectural assumptions:

- one YAML file defines one case,
- units are always SI,
- area distribution is at minimum tabulated,
- one droplet injection definition is sufficient for the MVP,
- steam wetness remains optional and may be constrained in MVP implementations.

---

## 10. Error Handling Strategy

### 10.1 Error Categories

Errors should be separated into the following categories:

- input parsing errors,
- schema validation errors,
- semantic configuration errors,
- unsupported model-selection errors,
- thermo backend errors,
- numerical solver failures,
- output writing errors,
- validation/reporting errors.

### 10.2 Error Propagation

Low-level modules should raise structured, specific errors. The application orchestration layer should enrich them with case context. The CLI should present concise user-facing summaries.

### 10.3 Numerical Failure Reporting

When numerical failure occurs, diagnostics should include as much of the following as practical:

- axial location,
- offending variable names,
- last valid state,
- selected model names,
- suggested likely causes.

### 10.4 Warning Strategy

Not all quality issues should abort the run. The architecture should distinguish between:

- fatal errors,
- recoverable warnings,
- informational diagnostics.

### 10.5 No Silent Fallbacks

The system should avoid hidden fallback behavior for unsupported fluids, unavailable property backends, or invalid breakup model names.

---

## 11. Testing Strategy

### 11.1 Unit Testing

Unit tests should cover isolated logic such as:

- YAML config validation,
- area interpolation,
- grid generation,
- thermo-provider behavior contracts,
- Weber number calculations,
- breakup decision rules,
- output serialization.

### 11.2 Integration Testing

Integration tests should cover:

- YAML-to-result pipeline,
- air case end-to-end run,
- steam interface selection behavior,
- output generation for CSV/JSON,
- plotting invocation from structured results.

### 11.3 Contract Testing

Interface-level tests should verify that all thermo providers and breakup models satisfy expected contracts. This is especially important for swappability.

### 11.4 Regression Testing

Fixed reference cases should be used to detect unintended changes in axial profiles, breakup triggers, or output structure.

### 11.5 Testing Constraints

Tests should not depend on interactive plotting, editor state, or manual inspection.

---

## 12. Validation Strategy

### 12.1 Purpose

Validation is distinct from software testing.

- testing checks correctness of software behavior,
- validation checks whether the simulator reproduces intended physical trends and accepted reference behavior within the MVP scope.

### 12.2 Validation Levels

The architecture should support three validation levels:

1. solver sanity validation,
2. physics trend validation,
3. reference-case validation.

### 12.3 Minimum MVP Validation Cases

The validation framework should support at least:

- constant-area gas-only case,
- converging/diverging geometry sanity case,
- zero-slip droplet case,
- breakup-trigger case,
- at least one steam-oriented case using the thermo abstraction.

### 12.4 Validation Outputs

Validation should produce structured reports with:

- case identity,
- expected trend statements,
- measured outcomes,
- pass/warn/fail status,
- notes on simplified-model limitations.

For quantitative-improvement workflow, validation outputs should additionally include:

- objective score summaries for baseline and optimized candidates,
- normalized sensitivity coefficients by parameter,
- uncertainty summary metrics (mean/std/95% CI) for sampled objectives.

### 12.5 Future Validation Extensions

The architecture should later support:

- comparison with published correlations,
- benchmark datasets,
- experimental reference import,
- automated validation dashboards.

### 12.6 Recommended Validation-Improvement Workflow

The architecture should support this ordered runtime workflow:

1. baseline validation execution,
2. one-at-a-time sensitivity analysis,
3. bounded parameter optimization,
4. objective uncertainty aggregation,
5. final baseline-vs-optimized comparison report.

---

## 13. Extension Strategy

### 13.1 Thermo Extension

The thermo layer is the primary extension point for:

- full IF97 integration,
- alternate steam libraries,
- additional working fluids.

This should require adding a new provider implementation without changing gas solver orchestration.

### 13.2 Breakup Extension

The breakup layer should support additional models through a registry or factory pattern. New breakup models should be selectable by configuration and should comply with the same interface.

### 13.3 Gas Solver Extension

The gas solver package should allow later addition of:

- loss models,
- choking-aware branches,
- fitted internal normal shocks for supported Laval nozzles,
- alternative quasi-1D formulations,
- iterative two-way coupling.

### 13.4 Droplet Extension

The droplet layer should allow future support for:

- evaporation,
- multiple representative droplet classes,
- population-based extensions,
- injection locations beyond the inlet.

### 13.5 Validation Extension

The validation package should grow independently from the solver core, allowing more reference cases without destabilizing production simulation logic.

### 13.6 Open Questions / Assumptions

Extension assumptions for MVP planning:

- IF97 may enter through a single steam-provider implementation first,
- breakup remains single-model in MVP but architecturally pluggable,
- two-way gas-droplet coupling is deferred,
- non-equilibrium steam behavior is deferred.

---

## 14. Technical Risks

### 14.1 Thermo Risk

Steam property integration may introduce complexity in valid-state handling, dependency management, and numerical stability near phase boundaries.

### 14.2 Numerical Robustness Risk

Quasi-1D compressible flow with strong pressure ratios, possible choking, fitted internal shocks, and simplified closure assumptions may lead to unstable or ambiguous branches if not carefully bounded.

### 14.3 Model-Coupling Risk

Even with one-way coupling, droplet behavior can become sensitive to gas-state errors, grid spacing, and abrupt breakup rules.

### 14.4 Breakup Simplification Risk

A simple Weber-threshold breakup model is appropriate for MVP but may produce nonphysical discontinuities or overly sharp diameter changes if not parameterized carefully.

### 14.5 Architecture Overdesign Risk

Because the project is still at MVP stage, there is a risk of designing too much abstraction too early. The implementation should preserve the architecture boundaries while keeping the first code path simple.

### 14.6 Validation Risk

Reference data for steam-driven droplet breakup may be limited. The architecture must therefore support trend-based validation and transparent documentation of model limitations.

### 14.7 Configuration Ambiguity Risk

If droplet loading, wetness interpretation, or steam-case boundaries remain underspecified, solver behavior may become inconsistent across cases. This reinforces the need for explicit config validation and documented assumptions.

---

## Appendix A. Architectural Summary

The architecture is a layered, interface-driven Python application with the following guiding structure:

- config translates YAML into validated internal models,
- domain models define the shared language of the system,
- thermo, breakup, and later drag implementations are swappable providers,
- gas and droplet solvers operate on stable interfaces and typed state models,
- IO and plotting consume result objects only,
- validation remains a first-class module rather than an afterthought,
- CLI remains a thin entry point over the application workflow.

This structure supports the MVP while keeping future IF97 integration and model expansion manageable.

---

## Appendix B. GUI Layer Architecture

> This appendix defines the architectural boundaries, module decomposition, data flow, and directory structure for the GUI extension described in [docs/spec.md — Appendix B](spec.md).

### B.1 GUI Layer Position

The GUI layer sits entirely above the existing application service boundary. It must not bypass or duplicate any solver, config, domain, IO, or plotting logic.

```
┌──────────────────────────────────────────────┐
│                  GUI Layer                   │
│  (browser / desktop front-end)               │
└──────────────────┬───────────────────────────┘
                   │  calls
┌──────────────────▼───────────────────────────┐
│           Application Service                │
│  (app/services.py — unchanged)               │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│   Config / Domain / Solvers / IO / Plotting  │
│   (all existing layers — unchanged)          │
└──────────────────────────────────────────────┘
```

### B.2 GUI Module Decomposition

The GUI package shall be organized under `src/supersonic_atomizer/gui/`.

| Module | Responsibility |
|---|---|
| `gui/fastapi_app.py` | FastAPI application factory; mounts routers, templates, and static assets |
| `gui/routers/index_router.py` | Serves the main single-page browser shell |
| `gui/routers/cases_router.py` | Project/case CRUD, rename, duplicate/export, move, and legacy-case materialization endpoints |
| `gui/routers/simulation_router.py` | Run/status/result endpoints and job polling contract |
| `gui/routers/units_router.py` | Unit preference REST endpoints |
| `gui/routers/chat_router.py` | Case-aware chat-history and LLM message endpoints |
| `gui/templates/index.html` | Main browser layout: project explorer, tabs, and report container |
| `gui/static/app.js` | Client-side state, tree/context-menu actions, drag/drop move, solve polling, report rendering, and chat panel behavior |
| `gui/static/app.css` | Browser layout, explorer styling, resize handles, report presentation, and chat panel styling |
| `gui/job_store.py` | Thread-safe in-memory simulation job store |
| `gui/session_store.py` | Server-side session store keyed by cookie/session id |
| `gui/multi_run.py` | GUI-side numeric-token parsing, sweep expansion, run labeling, and immutable run-snapshot helpers |
| `gui/case_store.py` | YAML-backed project/case persistence, migration, export, and rename/move operations |
| `gui/service_bridge.py` | Thin adapter between GUI events and the application service |
| `gui/unit_settings.py` | Display-unit groups, conversion helpers, and label formatting |
| `gui/chat_service.py` | Server-side LLM adapter that builds case-aware prompts and calls a configured provider |

Legacy Streamlit modules (`gui/app.py`, `gui/layout.py`, `gui/panels/`, `gui/pages/`, `gui/state.py`) remain in the repository as a compatibility path, but they are not the current primary browser architecture.

### B.3 Architectural Boundary Rules

- `gui/` modules must depend only on `app/services.py` and result/domain models.
- `gui/` modules must not import from `solvers/`, `thermo/`, `config/`, or `breakup/` directly.
- `gui/service_bridge.py` is the only permitted call site into the application service from the GUI.
- `gui/case_store.py` owns all case-persistence logic; no other GUI module reads/writes case files directly.
- Solver execution must remain non-blocking from the GUI perspective; a background thread or async pattern must be used.
- When a run starts, the GUI must snapshot the current case state into an immutable run payload; later case edits must not affect the running job.
- The GUI must handle `ApplicationService` errors and surface them as user-readable messages without exposing internal tracebacks.
- Multi-value numeric token parsing and sweep expansion belong to the GUI/application orchestration boundary only; they must not modify solver internals or case-store persistence rules.
- Overlay plotting must consume structured per-run `SimulationResult` objects only and must not recompute solver physics.
- Tree interactions such as right-click menus, rename, duplicate, export, delete, and drag/drop case moves must resolve to REST calls that in turn delegate to `case_store.py`; client code must not mutate the filesystem directly.
- Legacy flat-case canonicalization into `cases/default/` must occur at the case-store/router boundary, not in arbitrary front-end code.
- Report generation must remain a pure presentation concern in `gui/static/app.js`, consuming only the latest structured result payload, current form state, and display helpers.
- Sidebar resizing must remain a browser-layout concern only and must not change case-store, solver, or session semantics.
- Chat-panel resizing must remain a browser-layout concern only and must not alter case-store, solver, or run semantics.
- `gui/chat_service.py` must remain an integration boundary above the application service; it may read case-store data and latest completed GUI results but must not execute solver runs.
- Voice capture must remain browser-side transcription only unless a separately approved server-side audio-processing boundary is introduced later.

### B.4 GUI Data Flow

```
User action
  → GUI state update (gui/state.py)
  → gui/multi_run.py parses multi-value numeric tokens and expands immutable run payloads
  → gui/service_bridge.py calls ApplicationService once per expanded payload
  → ApplicationService returns one `SimulationRunResult` per expanded payload
  → GUI layer stores the per-run results and assembles overlay/table/report/chat-context view models
  → GUI pages re-render from state
    → post_graphs.py reads per-run result axial arrays → overlay plots
    → post_table.py reads per-run result axial arrays → aggregated table
    → solve.py reads diagnostics → status display
    → app.js report helpers read latest result + active form state → report sections
    → chat_router.py reads selected-case config + latest-result summary → chat_service.py → provider response
```

### B.5 Case Store Design

- Cases are stored in a local YAML-backed case store (default directory: `cases/`).
- The GUI organizes saved inputs as a two-level hierarchy: `Project > Case`.
- The canonical on-disk layout is `cases/<project>/<case>.yaml`; legacy flat cases in `cases/*.yaml` remain readable through the default project for backward compatibility.
- `case_store.py` provides project-aware create, list, load, save, delete, and rename operations.
- `case_store.py` also owns case duplication, case/project export, project deletion, and legacy flat-case migration into a target project.
- The canonical GUI storage layout materializes legacy flat cases into `cases/default/<case>.yaml` when the project tree is enumerated.
- Each case YAML file is structurally identical to the existing input format consumed by `config/loader.py`.
- The GUI never constructs YAML manually; it translates form state into the internal case model, which is then serialized by `case_store.py`.
- Multi-value numeric Conditions entries are not persisted as multi-valued YAML scalars; when users want to save a case, the persisted case remains a single solver-compatible case definition.
- The CLI exposes a maintenance command to migrate legacy `cases/*.yaml` files into `cases/<project>/` without bypassing the case-store boundary.
- The GUI explorer exposes project-scoped maintenance actions for creating/renaming/exporting/deleting a project and case-scoped actions for creating/renaming/duplicating/exporting/deleting individual cases.
- Case movement across projects is modeled as a case-store rename with `target_project` semantics, preserving the same ownership boundary as other mutations.
- The active project/case tree is a presentation of case-store state; expand/collapse state, context-menu state, and sidebar width remain session-local UI concerns.
- Chat history is session-local UI/application state keyed by browser session and selected case; it must not be persisted into case YAML files.

### B.6 Directory Structure Addition

```text
src/supersonic_atomizer/
  └─ gui/
      ├─ fastapi_app.py
      ├─ dependencies.py
      ├─ job_store.py
      ├─ session_store.py
      ├─ schemas.py
      ├─ unit_settings.py
      ├─ service_bridge.py
      ├─ case_store.py
      ├─ multi_run.py
      ├─ routers/
      │   ├─ index_router.py
      │   ├─ cases_router.py
        │   ├─ chat_router.py
      │   ├─ simulation_router.py
      │   └─ units_router.py
        ├─ chat_service.py
      ├─ templates/
      │   └─ index.html
      └─ static/
          ├─ app.css
          └─ app.js
cases/               ← default case-store directory root
  └─ <project>/
       └─ <case>.yaml
```

### B.7 Technology Selection Constraints

- Technology must be Python-only.
- Technology must not require a separate non-Python server process.
- Technology must support tabular input, form controls, and Matplotlib-compatible or equivalent plot rendering.
- Technology selection is finalized during Phase 23 planning before implementation begins.
- Candidates include Streamlit, Panel, Dash, and Tkinter; the choice must be documented in the task plan before any GUI code is written.

FastAPI is the current primary GUI architecture. Streamlit is retained as a legacy-compatible prototype/front-end path for compatibility and earlier GUI history.

### B.7.1 Selected Technology: Streamlit (legacy-compatible prototype — P23-T01)

**Selected framework:** Streamlit

**Version added:** streamlit==1.56.0 (added via `uv add streamlit`)

**Rationale:**

| Constraint | Streamlit assessment |
|---|---|
| Python-only developer API | All GUI code is pure Python; no JavaScript required. |
| No separate non-Python server | Streamlit runs its own Python (Tornado) server; no external non-Python process. |
| Tabular input | `st.data_editor` provides the editable $(x, A)$ table required by Pre Tab 2. |
| Form controls | Full widget set: `st.selectbox`, `st.number_input`, `st.slider`, etc. |
| Matplotlib rendering | `st.pyplot()` renders Matplotlib figures natively without conversion. |
| Browser-based | Launches in the default browser; no desktop toolkit required. |
| Non-blocking solver | `threading.Thread` + `st.session_state` isolates synchronous solver execution from the UI loop. |
| Development simplicity | Highest among candidates; no callback wiring or layout DSL needed. |

**Rejected alternatives:**

- **Panel:** More flexible but more complex API; not necessary for this application's scope.
- **Dash:** Uses a JavaScript/React front-end internally; adds complexity without benefit over Streamlit for this use case.
- **Tkinter:** Desktop-only (no browser); limited `st.data_editor` equivalent; higher embedding effort for Matplotlib.

**Non-blocking design resolution (risk B.8):**
The solver is invoked in a background `threading.Thread`. Completion status and results are stored in `st.session_state`. The UI polls state on rerun. The Run button is disabled by a session-state flag while the thread is alive.

> **Note (Phase 25):** Streamlit was the original Phase 23 prototype. It remains a legacy-compatible front-end path, but FastAPI is the current primary GUI architecture. See B.7.2 for the current architecture selection.

### B.7.2 Selected Technology: FastAPI (current primary GUI architecture — P25-T01)

**Selected framework:** FastAPI + uvicorn + Jinja2 templates

**Version added:** `fastapi>=0.115`, `uvicorn[standard]>=0.30`, `jinja2>=3.1` (added via `uv add`)

**Rationale:**

| Constraint | FastAPI assessment |
|---|---|
| Python-only developer API | All server-side code is pure Python; no Node.js build process required. |
| No separate non-Python server | Uvicorn is a pure-Python ASGI server; no external non-Python process. |
| Tabular input | HTML `<table>` with editable `<input>` elements; no framework dependency. |
| Form controls | Standard HTML form elements rendered by Jinja2 templates. |
| Matplotlib rendering | Figures serialised to base64 PNG and embedded in `<img>` tags via JSON API. |
| Browser-based | Launches in the default browser via uvicorn on localhost. |
| Non-blocking solver | `threading.Thread` started by `/api/simulation/run`; client polls `/api/simulation/status/{job_id}`. |
| REST API separation | Clean JSON API boundary keeps front-end logic separate from solver logic. |

**Rejected alternatives / retained paths (Phase 25):**

- **Streamlit (Phase 23):** Suitable for rapid PoC; retained as a legacy-compatible front-end path, not the primary architecture.
- **Dash:** Uses a JavaScript/React front-end internally; adds complexity without benefit over FastAPI for this use case.
- **Panel:** More flexible but more complex API; no benefit over FastAPI REST for this use case.

**Module additions (Phase 25):**

| Module | Responsibility |
|---|---|
| `gui/fastapi_app.py` | FastAPI application factory; mounts routers and static files |
| `gui/schemas.py` | Pydantic request/response schemas |
| `gui/job_store.py` | In-memory simulation job store (thread-safe) |
| `gui/session_store.py` | In-memory server-side session store keyed by cookie |
| `gui/plot_utils.py` | Matplotlib figure → base64 PNG conversion helpers |
| `gui/multi_run.py` | Multi-value numeric parsing, sweep expansion, run-label generation, and temporary run-snapshot helpers |
| `gui/dependencies.py` | FastAPI `Depends` helpers for session resolution |
| `gui/routers/index_router.py` | `GET /` → main HTML page |
| `gui/routers/cases_router.py` | Case CRUD REST endpoints |
| `gui/routers/simulation_router.py` | Simulation run/status/result REST endpoints |
| `gui/routers/units_router.py` | Unit preference REST endpoints |
| `gui/templates/index.html` | Jinja2 main HTML template |
| `gui/static/app.css` | Application stylesheet |
| `gui/static/app.js` | Vanilla JavaScript client logic |

**Reused with additive extensions (Phase 27):**
`gui/case_store.py`, `gui/service_bridge.py`, `gui/unit_settings.py`, `gui/state.py`,
`gui/pages/post_graphs.py` (`extract_plot_series`), `gui/pages/post_table.py` (`result_to_table_rows`, `generate_csv_content`),
`gui/pages/pre_conditions.py`, `gui/pages/pre_grid.py`, `gui/pages/solve.py`, `gui/panels/case_panel.py`.

**Current browser-UI additions (Phase 33):**

- `gui/templates/index.html` provides a tree-style `Project Explorer`, a dedicated `Report` tab, and a vertical resize handle for the explorer pane.
- `gui/static/app.js` owns tree rendering, context-menu dispatch, case drag/drop moves between projects, case/project rename/export/delete flows, and client-side report synthesis from the latest solve result.
- `gui/routers/cases_router.py` materializes legacy root cases into the canonical `default` project during project enumeration so the browser always sees one stable hierarchy.
- `gui/static/app.css` defines the explorer-tree interaction states, drag/drop affordances, resizable sidebar presentation, and report layout styling.

**Current browser-UI additions (Phase 34):**

- `gui/pages/post_graphs.py` and the FastAPI result path include `Area Profile` as a first-class plot built from `SimulationResult.gas_solution.area_values`.
- `gui/templates/index.html` and `gui/static/app.js` render the same `x` vs `Area` figure in the Grid tab so the preview and post-run graph surfaces stay aligned.
- A right-side chat panel is introduced as a resizable browser pane with ChatGPT-style turn layout, session-local history, text input, and browser speech-recognition input when available.
- `gui/routers/chat_router.py` and `gui/chat_service.py` provide the server-side LLM integration boundary, assembling selected-case context and latest-result summary without exposing provider credentials to the browser.

**Non-blocking design resolution (Phase 25):**
The solver is invoked in a `threading.Thread` started by `/api/simulation/run`. For multi-value Conditions input,
the thread sequentially executes one application-service run per expanded immutable payload. The aggregated job result
is stored in `JobStore` keyed by `job_id`. The browser polls `/api/simulation/status/{job_id}` every 800 ms until the
status changes to `completed` or `failed`, then fetches `/api/simulation/result/{job_id}`.

Run execution uses copy-on-run semantics: the submitted job receives an immutable snapshot of the case state, and later edits in the case store do not change an in-flight run.

To preserve case-store compatibility and avoid output-directory collisions, GUI-initiated expanded runs may disable production artifact writing in the submitted run snapshots and rely on structured `SimulationResult` objects plus GUI-side figure/table assembly for browser display.

### B.8 GUI Technical Risks

- **Blocking solver execution:** The simulation engine is synchronous; the GUI must not freeze during a run. Threading or async design must be resolved before implementation.
- **State management complexity:** Multi-tab GUI state is more complex than CLI; state model design must be completed before page modules are implemented.
- **Case-store conflicts:** If a user edits a case while a simulation is running, race conditions may arise. Write-locking or copy-on-run semantics must be defined.
- **Case-store conflicts:** Resolved by copy-on-run semantics; the running job consumes an immutable snapshot of the case state.
- **Technology lock-in:** The chosen GUI framework constrains the deployment model. The `service_bridge.py` boundary must be preserved so the framework can be swapped if needed.

### B.9 Unit Conversion Boundary

Unit conversions shall occur exclusively at the GUI display boundary.

**Rules:**

- `gui/unit_settings.py` owns all unit-group definitions, conversion factors (scale + offset), and formatting helpers.
- No conversion logic shall appear in solver, domain, IO, plotting, or config modules.
- `gui/pages/post_graphs.py` and `gui/pages/post_table.py` apply conversions by consuming `state.unit_preferences()` at the display boundary only.
- `gui/pages/pre_conditions.py` and `gui/pages/pre_grid.py` accept SI inputs only. No unit conversion is applied to user-entered condition values.
- All values stored in `GUIState` condition and grid fields remain in SI units.
- Unit preferences are stored as `str` fields in `GUIState` (one field per quantity group).
- Conversion formula: `display_value = si_value × scale + offset`. The offset is non-zero only for temperature (K to \u00b0C: offset = \u2212273.15).
- When `unit_preferences` is `None` or absent, all display helpers shall fall back to SI values with SI labels.

Refer to [Appendix C — Laval Nozzle Back-Pressure Sweep and p/p0 Validation](appendix_c.md) for the sweep utility architecture, CLI usage, and the trend-based `p/p_0` validation-report contract.
