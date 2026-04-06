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
- use thermo-provider interfaces rather than direct property formulas where possible,
- surface numerical diagnostics and failure conditions.

### 3.8 Droplet Solver Layer

Responsibilities:

- initialize droplet state from case inputs,
- compute slip velocity relative to gas,
- compute drag-driven droplet acceleration,
- update droplet velocity and size metrics along the grid,
- request breakup decisions from the breakup module.

### 3.9 Breakup Model Layer

Responsibilities:

- define the breakup interface,
- compute Weber-based breakup criteria,
- return updated droplet metrics and breakup indicators,
- allow later replacement by alternative models.

This layer shall remain fully pluggable.

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
- support regression-test case definitions,
- report validation summaries independent of CLI formatting.

### 3.13 Application Orchestration Layer

Responsibilities:

- coordinate config loading,
- instantiate geometry, thermo, and model providers,
- run gas and droplet solvers in sequence,
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
  - drag model, breakup model, thermo backend selection, optional parameters
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
8. Run gas solver.
9. Initialize droplet state at inlet or injection location.
10. March droplet solution along the gas-state field.
11. At each step, compute slip-driven quantities and call breakup model as needed.
12. Assemble final simulation result.
13. Run post-solve validation and sanity checks.
14. Write CSV and JSON outputs.
15. Generate plots.
16. Return run summary and exit status.

### 7.2 Gas-to-Droplet Dependency

For the MVP, the droplet solver depends on the gas solution, but the gas solver does not depend on droplet feedback. This preserves one-way coupling and simplifies the numerical sequence.

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

### 12.5 Future Validation Extensions

The architecture should later support:

- comparison with published correlations,
- benchmark datasets,
- experimental reference import,
- automated validation dashboards.

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

Quasi-1D compressible flow with strong pressure ratios, possible choking, and simplified closure assumptions may lead to unstable or ambiguous branches if not carefully bounded.

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
| `gui/app.py` | Application entry point; assembles and launches the GUI |
| `gui/layout.py` | Top-level layout: left panel + main area composition |
| `gui/panels/case_panel.py` | Left panel: case list, new case, open case |
| `gui/pages/pre_conditions.py` | Pre Tab 1: analysis condition form controls |
| `gui/pages/pre_grid.py` | Pre Tab 2: grid definition table and area preview |
| `gui/pages/solve.py` | Solve tab: run button, convergence settings, status, history plot |
| `gui/pages/post_graphs.py` | Post Tab 1: axial profile plots |
| `gui/pages/post_table.py` | Post Tab 2: results table and CSV export |
| `gui/case_store.py` | Case persistence: save/load case state across sessions |
| `gui/service_bridge.py` | Thin adapter between GUI events and the application service |
| `gui/state.py` | GUI-side reactive or session state model |

### B.3 Architectural Boundary Rules

- `gui/` modules must depend only on `app/services.py` and result/domain models.
- `gui/` modules must not import from `solvers/`, `thermo/`, `config/`, or `breakup/` directly.
- `gui/service_bridge.py` is the only permitted call site into the application service from the GUI.
- `gui/case_store.py` owns all case-persistence logic; no other GUI module reads/writes case files directly.
- Solver execution must remain non-blocking from the GUI perspective; a background thread or async pattern must be used.
- The GUI must handle `ApplicationService` errors and surface them as user-readable messages without exposing internal tracebacks.

### B.4 GUI Data Flow

```
User action
  → GUI state update (gui/state.py)
  → gui/service_bridge.py calls ApplicationService
  → ApplicationService returns SimulationRunResult
  → gui/state.py stores result
  → GUI pages re-render from state
    → post_graphs.py reads result axial arrays → plots
    → post_table.py reads result axial arrays → table
    → solve.py reads diagnostics → status display
```

### B.5 Case Store Design

- Cases are stored as YAML files in a configurable local case directory (default: `cases/`).
- `case_store.py` provides create, list, load, and save operations.
- Each case YAML file is structurally identical to the existing input format consumed by `config/loader.py`.
- The GUI never constructs YAML manually; it translates form state into the internal case model, which is then serialized by `case_store.py`.

### B.6 Directory Structure Addition

```text
src/supersonic_atomizer/
  └─ gui/
      ├─ app.py
      ├─ layout.py
      ├─ state.py
      ├─ service_bridge.py
      ├─ case_store.py
      ├─ panels/
      │   └─ case_panel.py
      └─ pages/
          ├─ pre_conditions.py
          ├─ pre_grid.py
          ├─ solve.py
          ├─ post_graphs.py
          └─ post_table.py
cases/               ← default case-store directory
```

### B.7 Technology Selection Constraints

- Technology must be Python-only.
- Technology must not require a separate non-Python server process.
- Technology must support tabular input, form controls, and Matplotlib-compatible or equivalent plot rendering.
- Technology selection is finalized during Phase 23 planning before implementation begins.
- Candidates include Streamlit, Panel, Dash, and Tkinter; the choice must be documented in the task plan before any GUI code is written.

### B.7.1 Selected Technology: Streamlit (decided — P23-T01)

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

### B.8 GUI Technical Risks

- **Blocking solver execution:** The simulation engine is synchronous; the GUI must not freeze during a run. Threading or async design must be resolved before implementation.
- **State management complexity:** Multi-tab GUI state is more complex than CLI; state model design must be completed before page modules are implemented.
- **Case-store conflicts:** If a user edits a case while a simulation is running, race conditions may arise. Write-locking or copy-on-run semantics must be defined.
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
