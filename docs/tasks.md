# Supersonic Atomizer Simulator Task Plan

This task plan uses [docs/spec.md](docs/spec.md) and [docs/architecture.md](docs/architecture.md) as the source of truth.

Rules for this plan:

- Tasks are implementation-ready but code-free.
- Tasks are organized by phase.
- Each task is small, testable, and dependency-aware.
- MVP scope is limited to quasi-1D internal flow, representative droplet transport, simple Weber-threshold breakup, CLI execution, YAML input, CSV/JSON output, and Matplotlib plotting.

---

## Phase 1. Project Bootstrap

### Definition of Done

Phase 1 is done when the repository has an agreed project skeleton, package layout, basic development conventions, and documentation links aligned with the approved spec and architecture.

- [x] **P1-T01 — Create project skeleton**
  - **Purpose:** Establish the top-level directory structure required by the architecture.
  - **Dependencies:** None.
  - **Completion criteria:** The agreed directories for source, docs, tests, examples, and outputs are defined and documented.

- [x] **P1-T02 — Define package naming and module boundaries**
  - **Purpose:** Lock down the Python package name and map architecture layers to concrete module groups.
  - **Dependencies:** P1-T01.
  - **Completion criteria:** A written module map exists covering config, domain, thermo, geometry, grid, solvers, breakup, IO, plotting, validation, app, and CLI.

- [x] **P1-T03 — Define development tooling baseline**
  - **Purpose:** Decide the baseline tools for environment management, testing, linting, and formatting without implementing features yet.
  - **Dependencies:** P1-T01.
  - **Completion criteria:** Tooling decisions are documented and consistent with Python-only and VS Code usage.

- [x] **P1-T04 — Define error category taxonomy**
  - **Purpose:** Agree on the application-level error categories before implementation spreads error handling across modules.
  - **Dependencies:** P1-T02.
  - **Completion criteria:** Input, configuration, model-selection, thermo, numerical, output, and validation error categories are documented.

- [x] **P1-T05 — Define run artifact conventions**
  - **Purpose:** Standardize output directory layout, file naming, and run metadata conventions.
  - **Dependencies:** P1-T02.
  - **Completion criteria:** Expected locations and names for CSV, JSON, plots, and logs/diagnostics are documented.

---

## Phase 2. Config and Domain Models

### Definition of Done

Phase 2 is done when YAML input structure, internal case models, and result/diagnostic models are fully specified and traceable to spec requirements.

- [x] **P2-T01 — Define raw YAML schema structure**
  - **Purpose:** Translate spec inputs into a stable external configuration shape.
  - **Dependencies:** P1-T02.
  - **Completion criteria:** The YAML sections and required/optional fields are fully documented, including fluid, boundary conditions, geometry, droplet injection, model selection, and outputs.

- [x] **P2-T02 — Define semantic validation rules**
  - **Purpose:** Specify which parsed inputs are physically or structurally invalid.
  - **Dependencies:** P2-T01, P1-T04.
  - **Completion criteria:** Validation rules exist for required fields, allowed values, SI units, positive pressures, positive temperatures, valid diameters, valid grid extents, and valid area data.

- [x] **P2-T03 — Define case configuration data models**
  - **Purpose:** Specify the internal typed models representing validated case inputs.
  - **Dependencies:** P2-T01.
  - **Completion criteria:** Internal models are defined for full case config, fluid config, boundary conditions, geometry config, droplet injection config, model selection config, and output config.

- [x] **P2-T04 — Define solver state models**
  - **Purpose:** Establish the internal representation of gas state, droplet state, and thermo state used across solver layers.
  - **Dependencies:** P2-T03.
  - **Completion criteria:** State model definitions exist for thermo state, local gas state, gas solution, local droplet state, droplet solution, and breakup decision.

- [x] **P2-T05 — Define result and diagnostics models**
  - **Purpose:** Standardize how final outputs, warnings, and numerical status are represented.
  - **Dependencies:** P2-T04, P1-T04.
  - **Completion criteria:** Result models are defined for simulation result, run diagnostics, validation report, and output metadata.

- [x] **P2-T06 — Define config translation flow**
  - **Purpose:** Document the processing path from raw YAML to validated internal models.
  - **Dependencies:** P2-T01, P2-T02, P2-T03.
  - **Completion criteria:** A documented sequence exists for parse, schema validation, semantic validation, defaults application, and translation into internal models.

- [x] **P2-T07 — Define defaults policy**
  - **Purpose:** Make implicit assumptions explicit and centralized.
  - **Dependencies:** P2-T01, P2-T03.
  - **Completion criteria:** The allowed defaults and non-default-required fields are documented, including default breakup model, default plotting behavior, and optional wetness handling.

---

## Phase 3. Geometry and Grid

### Definition of Done

Phase 3 is done when the simulator has a fully specified geometry and axial-grid foundation that can supply consistent $x$ and $A(x)$ data to downstream solvers.

- [x] **P3-T01 — Define axial geometry representation**
  - **Purpose:** Establish how the duct/nozzle domain is represented internally.
  - **Dependencies:** P2-T03.
  - **Completion criteria:** Geometry representation includes axial range, area profile source, and geometry metadata required by the solver.

- [x] **P3-T02 — Define area profile abstraction**
  - **Purpose:** Separate solver usage of area from the original input format.
  - **Dependencies:** P3-T01.
  - **Completion criteria:** A documented abstraction exists for querying area consistently along the axial coordinate.

- [x] **P3-T03 — Define tabulated area interpolation behavior**
  - **Purpose:** Specify how user-provided $(x, A)$ data is interpreted between points.
  - **Dependencies:** P3-T02.
  - **Completion criteria:** The interpolation method, boundary behavior, monotonicity expectations, and invalid-input rules are documented.

- [x] **P3-T04 — Define axial grid model**
  - **Purpose:** Standardize the computational grid used by the gas and droplet solvers.
  - **Dependencies:** P3-T01.
  - **Completion criteria:** Grid representation covers node positions, indexing convention, spacing, and metadata needed for marching or evaluation.

- [x] **P3-T05 — Define grid generation rules**
  - **Purpose:** Ensure the solver receives a valid and reproducible discretization from case inputs.
  - **Dependencies:** P3-T04, P2-T02.
  - **Completion criteria:** Grid generation rules are documented for extent validation, cell count handling, and failure conditions.

- [x] **P3-T06 — Define geometry/grid diagnostics**
  - **Purpose:** Enable early detection of malformed geometry or grid issues before solver execution.
  - **Dependencies:** P3-T03, P3-T05.
  - **Completion criteria:** Diagnostic checks are defined for invalid ranges, nonpositive area values, inconsistent table lengths, and degenerate grids.

---

## Phase 4. Thermodynamic Abstraction

### Definition of Done

Phase 4 is done when the fluid-property contract is defined, air and steam provider responsibilities are clear, and steam IF97 support can later be added or swapped without changing solver orchestration.

- [x] **P4-T01 — Define thermo provider interface**
  - **Purpose:** Create the boundary the gas solver uses for all fluid-property access.
  - **Dependencies:** P2-T04.
  - **Completion criteria:** The required thermo operations, inputs, outputs, metadata, and error conditions are documented.

- [x] **P4-T02 — Define air thermo provider responsibilities**
  - **Purpose:** Specify the MVP air-property behavior compatible with the thermo interface.
  - **Dependencies:** P4-T01.
  - **Completion criteria:** The air provider assumptions, supported states, and expected property outputs are documented.

- [x] **P4-T03 — Define steam thermo provider interface contract**
  - **Purpose:** Reserve a clean swap point for future IF97-based steam handling.
  - **Dependencies:** P4-T01.
  - **Completion criteria:** Steam provider responsibilities, expected state queries, validity constraints, and equilibrium assumptions are documented.

- [x] **P4-T04 — Define thermo backend selection strategy**
  - **Purpose:** Determine how the application chooses the correct provider from configuration.
  - **Dependencies:** P2-T03, P4-T01, P4-T03.
  - **Completion criteria:** Selection rules are documented for air, steam, unsupported names, and future alternate steam backends.

- [x] **P4-T05 — Define thermo failure behavior**
  - **Purpose:** Prevent property errors from becoming ambiguous solver failures.
  - **Dependencies:** P4-T01, P1-T04.
  - **Completion criteria:** Error handling is documented for invalid states, backend absence, out-of-range states, and unsupported phase-region requests.

- [x] **P4-T06 — Define thermo contract tests**
  - **Purpose:** Ensure swappable thermo implementations can be verified against the same interface requirements.
  - **Dependencies:** P4-T01, P4-T02, P4-T03.
  - **Completion criteria:** A documented set of interface-level test expectations exists for all thermo providers.

---

## Phase 5. Quasi-1D Gas Solver

### Definition of Done

Phase 5 is done when the gas-solver workflow, state updates, boundary-condition handling, diagnostics, and expected outputs are fully specified for the MVP quasi-1D internal flow problem.

- [x] **P5-T01 — Define gas solver inputs and outputs**
  - **Purpose:** Formalize the gas solver contract relative to grid, geometry, thermo, and boundary conditions.
  - **Dependencies:** P3-T04, P4-T01, P2-T04.
  - **Completion criteria:** Solver inputs and required outputs are documented, including pressure, temperature, density, velocity, and Mach number along $x$.

- [x] **P5-T02 — Define gas solver formulation boundaries**
  - **Purpose:** Clarify what the MVP gas solver does and does not attempt to model.
  - **Dependencies:** P5-T01.
  - **Completion criteria:** The documented formulation includes steady quasi-1D behavior and explicitly excludes non-MVP physics such as high-fidelity turbulence and full multiphase CFD.

- [x] **P5-T03 — Define gas solver sequence and state update logic**
  - **Purpose:** Provide a clear implementation path for advancing the gas solution.
  - **Dependencies:** P5-T01, P3-T04, P4-T01.
  - **Completion criteria:** A step-by-step solver sequence is documented from initialized state through axial solution assembly.

- [x] **P5-T04 — Define boundary-condition handling**
  - **Purpose:** Specify how inlet total conditions and outlet static pressure are used consistently.
  - **Dependencies:** P5-T01, P2-T03.
  - **Completion criteria:** The expected role of inlet total pressure, inlet total temperature, and outlet static pressure is documented, including invalid combinations and open assumptions.

- [x] **P5-T05 — Define gas diagnostics and failure criteria**
  - **Purpose:** Make numerical problems visible and actionable.
  - **Dependencies:** P5-T03, P1-T04.
  - **Completion criteria:** Failure and warning rules are documented for nonphysical states, branch ambiguity, failed closure, and incomplete solution progression.

- [x] **P5-T06 — Define gas-only validation cases**
  - **Purpose:** Prepare the minimum reference behavior needed before droplet coupling is added.
  - **Dependencies:** P5-T01, P5-T02.
  - **Completion criteria:** Validation case definitions exist for constant-area gas-only and converging/diverging geometry sanity behavior.

---

## Phase 6. Droplet Transport Solver

### Definition of Done

Phase 6 is done when the representative droplet transport model is fully specified against the gas solution, including slip velocity, drag-driven acceleration, and axial droplet-state evolution.

- [x] **P6-T01 — Define droplet solver contract**
  - **Purpose:** Formalize how the droplet solver consumes gas results and droplet injection inputs.
  - **Dependencies:** P2-T04, P5-T01.
  - **Completion criteria:** Inputs, outputs, and expected droplet state variables are documented.

- [x] **P6-T02 — Define droplet injection assumptions**
  - **Purpose:** Make the MVP representation of droplet initial conditions explicit.
  - **Dependencies:** P2-T03, P6-T01.
  - **Completion criteria:** Injection location, initial velocity, initial mean diameter, and initial maximum diameter handling are documented.

- [x] **P6-T03 — Define slip velocity and drag evaluation flow**
  - **Purpose:** Specify the local calculations required to update droplet motion.
  - **Dependencies:** P6-T01, P4-T01.
  - **Completion criteria:** The sequence for gas-state lookup, slip evaluation, drag input preparation, and droplet update is documented.

- [x] **P6-T04 — Define drag model abstraction**
  - **Purpose:** Prevent drag logic from being hard-wired into the droplet solver core.
  - **Dependencies:** P6-T03.
  - **Completion criteria:** A documented drag-model boundary exists, with the MVP default identified and future replacement supported.

- [x] **P6-T05 — Define droplet marching/update strategy**
  - **Purpose:** Ensure droplet states advance consistently along the axial grid.
  - **Dependencies:** P3-T04, P6-T03.
  - **Completion criteria:** The axial update sequence and expected ordering of velocity, Weber number, and diameter-related evaluations are documented.

- [x] **P6-T06 — Define droplet diagnostics and bounds checks**
  - **Purpose:** Catch unstable or nonphysical droplet states early.
  - **Dependencies:** P6-T05, P1-T04.
  - **Completion criteria:** Checks are documented for negative velocity where invalid, negative diameter, NaN values, and inconsistent droplet metrics.

- [x] **P6-T07 — Define droplet transport validation cases**
  - **Purpose:** Establish baseline validation before breakup effects are enabled.
  - **Dependencies:** P6-T01, P6-T02, P6-T05.
  - **Completion criteria:** Validation definitions exist for zero-slip or near-zero-slip behavior and a case with expected slip-driven acceleration.

---

## Phase 7. Breakup Model

### Definition of Done

Phase 7 is done when the breakup interface, MVP Weber-threshold model behavior, and integration with the droplet solver are fully specified and independently testable.

- [x] **P7-T01 — Define breakup model interface**
  - **Purpose:** Create a pluggable boundary between droplet transport and breakup logic.
  - **Dependencies:** P2-T04, P6-T01.
  - **Completion criteria:** The breakup model inputs, outputs, parameter requirements, and diagnostic outputs are documented.

- [x] **P7-T02 — Define Weber number calculation contract**
  - **Purpose:** Standardize the quantity driving the MVP breakup criterion.
  - **Dependencies:** P7-T01.
  - **Completion criteria:** The Weber number definition, required inputs, units, and evaluation timing are documented.

- [x] **P7-T03 — Define MVP Weber-threshold breakup behavior**
  - **Purpose:** Specify exactly how breakup is triggered and how droplet metrics change.
  - **Dependencies:** P7-T01, P7-T02.
  - **Completion criteria:** Trigger logic, threshold handling, and diameter-update rules for mean and maximum diameters are documented.

- [x] **P7-T04 — Define breakup model registry/selection strategy**
  - **Purpose:** Make breakup model choice configuration-driven and extensible.
  - **Dependencies:** P2-T03, P7-T01.
  - **Completion criteria:** Model selection rules are documented for the MVP model, unsupported names, and future plug-in additions.

- [x] **P7-T05 — Define breakup integration sequence in droplet solver**
  - **Purpose:** Clarify where breakup decisions occur during the droplet update cycle.
  - **Dependencies:** P6-T05, P7-T03.
  - **Completion criteria:** The update order between droplet transport calculations and breakup application is documented.

- [x] **P7-T06 — Define breakup validation cases**
  - **Purpose:** Verify expected threshold behavior and non-trigger behavior.
  - **Dependencies:** P7-T02, P7-T03.
  - **Completion criteria:** Validation definitions exist for no-breakup and breakup-trigger cases with expected diameter-change trends.

---

## Phase 8. Outputs and Plotting

### Definition of Done

Phase 8 is done when structured simulation results can be serialized to CSV and JSON and major axial profiles can be plotted consistently from result models alone.

- [x] **P8-T01 — Define output result schema**
  - **Purpose:** Standardize the final data contract for writers and plotters.
  - **Dependencies:** P2-T05, P5-T01, P6-T01, P7-T01.
  - **Completion criteria:** The final output schema includes core axial fields, metadata, diagnostics, and breakup indicators.

- [x] **P8-T02 — Define CSV export content and format**
  - **Purpose:** Specify flat-file output behavior for tabular results.
  - **Dependencies:** P8-T01.
  - **Completion criteria:** Column definitions, ordering, naming, and file naming conventions are documented.

- [x] **P8-T03 — Define JSON export content and format**
  - **Purpose:** Specify structured machine-readable output behavior.
  - **Dependencies:** P8-T01.
  - **Completion criteria:** JSON structure includes metadata, settings summary, numerical results, and diagnostics.

- [x] **P8-T04 — Define plot set for MVP**
  - **Purpose:** Lock the minimum required visual outputs from the spec.
  - **Dependencies:** P8-T01.
  - **Completion criteria:** Required plots are documented for pressure, temperature, working-fluid velocity, droplet velocity, slip velocity, surface tension, Mach number, droplet mean diameter, droplet maximum diameter, and Weber number.

- [x] **P8-T05 — Define plotting input contract**
  - **Purpose:** Keep plotting independent of solver internals.
  - **Dependencies:** P8-T01, P8-T04.
  - **Completion criteria:** Plotting is defined to consume only structured result objects and output settings.

- [x] **P8-T06 — Define output and plotting failure behavior**
  - **Purpose:** Ensure export issues are distinguishable from solver issues.
  - **Dependencies:** P8-T02, P8-T03, P8-T05, P1-T04.
  - **Completion criteria:** Output-write and plot-generation error rules are documented with expected run-summary behavior.

---

## Phase 9. Tests

### Definition of Done

Phase 9 is done when unit, integration, contract, regression, and validation-oriented test plans exist for all MVP-critical modules and interfaces.

- [x] **P9-T01 — Define unit test matrix**
  - **Purpose:** Map low-level modules to isolated tests.
  - **Dependencies:** P2-T02, P3-T05, P4-T06, P7-T02.
  - **Completion criteria:** A documented unit test matrix exists for config validation, geometry interpolation, grid generation, thermo contracts, Weber number evaluation, and output formatting.

- [x] **P9-T02 — Define integration test matrix**
  - **Purpose:** Cover the end-to-end behavior of the MVP pipeline.
  - **Dependencies:** P5-T06, P6-T07, P7-T06, P8-T03.
  - **Completion criteria:** Integration test definitions exist for YAML-to-result execution, air case pipeline, steam-provider selection behavior, and output generation.

- [x] **P9-T03 — Define contract tests for swappable interfaces**
  - **Purpose:** Protect extensibility promises for thermo and breakup layers.
  - **Dependencies:** P4-T06, P7-T04.
  - **Completion criteria:** Contract-test expectations are documented for all thermo providers and breakup models.

- [x] **P9-T04 — Define regression case set**
  - **Purpose:** Prevent unintended behavior drift across refactors.
  - **Dependencies:** P5-T06, P6-T07, P7-T06.
  - **Completion criteria:** A fixed set of reference case definitions and tracked outputs is documented.

- [x] **P9-T05 — Define test data organization**
  - **Purpose:** Keep test cases, reference results, and validation artifacts manageable.
  - **Dependencies:** P9-T01, P9-T04.
  - **Completion criteria:** The storage and naming conventions for unit fixtures, integration cases, and validation references are documented.

---

## Phase 10. Examples and Documentation

### Definition of Done

Phase 10 is done when the MVP has example case definitions, user-facing run guidance, and internal developer guidance aligned with the approved architecture and test strategy.

- [x] **P10-T01 — Define MVP example case set**
  - **Purpose:** Identify representative cases that demonstrate the supported workflow.
  - **Dependencies:** P5-T06, P6-T07, P7-T06.
  - **Completion criteria:** At least one air case and one steam-oriented case definition are documented, along with their intended purpose.

- [x] **P10-T02 — Define example YAML conventions**
  - **Purpose:** Ensure sample cases clearly reflect the supported schema and assumptions.
  - **Dependencies:** P2-T01, P10-T01.
  - **Completion criteria:** Example-case conventions are documented for required fields, optional fields, and model-selection clarity.

- [x] **P10-T03 — Define user run workflow documentation**
  - **Purpose:** Describe the intended CLI-driven usage sequence without exposing implementation details.
  - **Dependencies:** P8-T02, P8-T03, P8-T04.
  - **Completion criteria:** User workflow documentation exists for providing a YAML case, running the simulator, and locating outputs.

- [x] **P10-T04 — Define developer extension guidance**
  - **Purpose:** Help future contributors add thermo providers, breakup models, and validation cases safely.
  - **Dependencies:** P4-T06, P7-T04, P9-T03.
  - **Completion criteria:** Extension guidance is documented for thermo, breakup, and validation modules.

- [x] **P10-T05 — Define assumptions and limitations summary**
  - **Purpose:** Ensure the MVP boundaries remain explicit in user and developer documentation.
  - **Dependencies:** P5-T02, P6-T02, P7-T03.
  - **Completion criteria:** A concise limitations summary exists covering quasi-1D scope, one-way coupling, simple breakup, and excluded physics.

---

## Cross-Phase Notes

### Sequencing Constraints

- Phase 1 must complete before detailed implementation begins.
- Phase 2 should complete before solver implementation begins.
- Phase 3 and Phase 4 should complete before the gas solver is implemented.
- Phase 5 should complete before full droplet transport work proceeds.
- Phase 6 should complete before breakup integration is finalized.
- Phase 7 should complete before output schemas are finalized.
- Phase 8 should complete before end-to-end examples are considered complete.
- Phase 9 and Phase 10 may overlap late in MVP work but should not bypass unresolved architecture boundaries.

### MVP Exit Conditions

The overall MVP planning effort is complete when:

- all phases have documented Definitions of Done,
- all tasks have clear dependencies and completion criteria,
- the task set remains aligned to [docs/spec.md](docs/spec.md) and [docs/architecture.md](docs/architecture.md),
- no task introduces out-of-scope physics or premature non-MVP features.

---

## Phase 11. Runtime Config Foundations

### Definition of Done

Phase 11 is done when one YAML case file can be loaded, validated, defaulted, and translated into internal runtime configuration models through the config layer only, with explicit startup-stage errors and focused tests.

- [x] **P11-T01 — Create runtime config module scaffold**
  - **Purpose:** Establish the concrete runtime module structure for config loading, defaults, schema validation, semantic validation, and translation.
  - **Dependencies:** P1-T02, P2-T06.
  - **Completion criteria:** Runtime config modules and package exports exist with responsibilities aligned to the documented config flow and architecture boundaries.

- [x] **P11-T02 — Implement YAML case loader**
  - **Purpose:** Load one case file from disk into a raw configuration structure before validation and translation.
  - **Dependencies:** P11-T01, P2-T01.
  - **Completion criteria:** A valid YAML case can be parsed into a raw in-memory structure, and parse/file errors are surfaced explicitly with tests for valid and invalid inputs.

- [x] **P11-T03 — Implement config defaults application**
  - **Purpose:** Centralize runtime defaults before semantic translation so assumptions do not spread across downstream modules.
  - **Dependencies:** P11-T02, P2-T07.
  - **Completion criteria:** Documented defaults are applied in the config layer only, and tests cover defaulted and non-default-required fields.

- [x] **P11-T04 — Implement raw schema validation**
  - **Purpose:** Enforce required YAML sections and field presence before semantic validation begins.
  - **Dependencies:** P11-T02, P2-T01.
  - **Completion criteria:** Invalid raw config structure is rejected with explicit input/configuration errors, and tests cover required sections, required fields, and allowed value checks.

- [x] **P11-T05 — Implement semantic config validation**
  - **Purpose:** Reject structurally valid but nonphysical or unsupported runtime inputs before they reach internal models.
  - **Dependencies:** P11-T03, P11-T04, P2-T02.
  - **Completion criteria:** Semantic validation rejects nonphysical values and unsupported selections defined by the spec, and tests cover positive/negative validation cases.

- [x] **P11-T06 — Implement config translation to internal runtime models**
  - **Purpose:** Translate validated config data into typed internal case-definition models used by downstream runtime code.
  - **Dependencies:** P11-T05, P12-T01.
  - **Completion criteria:** Validated config is translated into internal runtime configuration models without leaking raw YAML structure downstream, and tests cover end-to-end config translation for representative cases.

---

## Phase 12. Runtime Domain Models

### Definition of Done

Phase 12 is done when internal runtime data models exist for case configuration, solver states, results, diagnostics, and error categories, and these models can be imported and used by config and later solver code with focused tests.

- [x] **P12-T01 — Implement runtime case-configuration models**
  - **Purpose:** Create the typed runtime models representing validated case inputs.
  - **Dependencies:** P2-T03.
  - **Completion criteria:** Runtime models exist for full case config, fluid config, boundary conditions, geometry config, droplet injection config, model selection config, and output config, with tests for construction and field semantics.

- [x] **P12-T02 — Implement runtime solver-state models**
  - **Purpose:** Create the typed runtime models used by gas, droplet, thermo, and breakup layers.
  - **Dependencies:** P12-T01, P2-T04.
  - **Completion criteria:** Runtime models exist for thermo state, gas state, gas solution, droplet state, droplet solution, and breakup decision, with tests for construction and basic invariants.

- [x] **P12-T03 — Implement runtime result and diagnostics models**
  - **Purpose:** Create the typed runtime models for final results, warnings, and validation/reporting outputs.
  - **Dependencies:** P12-T02, P2-T05.
  - **Completion criteria:** Runtime models exist for simulation result, run diagnostics, validation report, and output metadata, with tests for field presence and structure alignment.

- [x] **P12-T04 — Implement runtime error classes**
  - **Purpose:** Convert the documented error taxonomy into concrete runtime exception types usable across config, thermo, solver, IO, and validation boundaries.
  - **Dependencies:** P1-T04, P12-T03.
  - **Completion criteria:** Concrete runtime error classes exist for the documented error categories, and tests verify their availability and intended categorization.

---

## Phase 13. Geometry and Grid Runtime Foundations

### Definition of Done

Phase 13 is done when runtime geometry and grid objects can be constructed from validated internal models, queried consistently along $x$, and validated through focused unit tests.

- [x] **P13-T01 — Implement runtime axial-grid model and builder**
  - **Purpose:** Create the runtime axial-grid object and grid-construction path used by downstream gas and droplet solvers.
  - **Dependencies:** P3-T04, P3-T05, P12-T01.
  - **Completion criteria:** A runtime axial-grid model and construction function exist for validated grid inputs, and tests cover node ordering, extent handling, and invalid-grid rejection.

- [x] **P13-T02 — Implement runtime tabulated area-profile model**
  - **Purpose:** Create the runtime area-profile object that stores validated tabulated area data and exposes consistent area queries.
  - **Dependencies:** P3-T01, P3-T02, P12-T01.
  - **Completion criteria:** A runtime area-profile model exists for tabulated $(x, A)$ data, and tests cover construction, storage, and nonpositive-area rejection.

- [x] **P13-T03 — Implement area interpolation behavior**
  - **Purpose:** Realize the documented interpolation behavior used by the geometry abstraction.
  - **Dependencies:** P13-T02, P3-T03.
  - **Completion criteria:** Runtime interpolation behavior matches the documented rules for in-range and boundary queries, and tests cover representative interpolation cases.

- [x] **P13-T04 — Implement runtime geometry assembly**
  - **Purpose:** Build the runtime geometry object that combines domain metadata and area-profile access for solver use.
  - **Dependencies:** P13-T01, P13-T03, P3-T01.
  - **Completion criteria:** A runtime geometry model can be assembled from validated config models and queried consistently by downstream code, with tests for geometry/grid alignment.

- [x] **P13-T05 — Implement geometry/grid diagnostics checks**
  - **Purpose:** Enforce runtime checks for malformed geometry and degenerate grid conditions before solver execution.
  - **Dependencies:** P13-T04, P3-T06, P12-T04.
  - **Completion criteria:** Runtime diagnostics reject documented malformed geometry/grid cases with explicit errors, and tests cover invalid ranges, inconsistent lengths, and degenerate grids.

---

## Phase 14. Thermo Runtime Foundations

### Definition of Done

Phase 14 is done when the runtime thermo interface exists, the air provider is implemented behind that interface, backend selection works for the supported foundation path, and unsupported thermo paths fail explicitly with focused tests.

- [x] **P14-T01 — Implement runtime thermo provider interface**
  - **Purpose:** Create the concrete runtime interface or abstract contract used by gas-side code for property access.
  - **Dependencies:** P4-T01, P12-T02.
  - **Completion criteria:** A runtime thermo-provider contract exists with the documented property-access operations and metadata shape, and tests verify interface-level expectations.

- [x] **P14-T02 — Implement runtime air thermo provider**
  - **Purpose:** Provide the first concrete thermo implementation for the MVP executable foundation path.
  - **Dependencies:** P14-T01, P4-T02.
  - **Completion criteria:** A runtime air thermo provider exists behind the thermo interface, and tests cover representative valid states, invalid states, and SI-unit-consistent outputs.

- [x] **P14-T03 — Implement thermo backend selection for supported foundation cases**
  - **Purpose:** Resolve the correct thermo provider from validated internal configuration without coupling runtime code to one backend directly.
  - **Dependencies:** P14-T02, P4-T04, P12-T01.
  - **Completion criteria:** Runtime backend selection resolves supported air cases and rejects unsupported or unavailable thermo selections explicitly, with tests for positive and negative selection behavior.

- [x] **P14-T04 — Implement thermo failure propagation rules**
  - **Purpose:** Ensure runtime thermo failures remain distinguishable from unrelated config or solver failures.
  - **Dependencies:** P14-T03, P4-T05, P12-T04.
  - **Completion criteria:** Runtime thermo failures surface through the documented error categories and tests cover invalid-state, unsupported-backend, and out-of-range behavior.

---

## Phase 15. Application and CLI Scaffolding

### Definition of Done

Phase 15 is done when a thin runtime application and CLI scaffold can accept a case path, invoke config loading and startup-stage dependency construction through the documented boundaries, and return structured startup status without embedding solver logic in the CLI.

- [x] **P15-T01 — Create application orchestration scaffold**
  - **Purpose:** Establish the runtime application service boundary that coordinates config loading, dependency selection, and later solver orchestration.
  - **Dependencies:** P12-T03, P14-T03.
  - **Completion criteria:** Application-layer runtime modules and service entry points exist with responsibilities aligned to the architecture, and tests cover basic import and startup wiring behavior.

- [x] **P15-T02 — Implement startup-stage run service flow**
  - **Purpose:** Realize the pre-solver portion of the documented application workflow using the config and thermo foundation layers.
  - **Dependencies:** P15-T01, P11-T06, P13-T05, P14-T04.
  - **Completion criteria:** A runtime service can load a case, construct validated startup-stage dependencies, and return structured startup status or explicit failure context, with tests for success and startup failure paths.

- [x] **P15-T03 — Create thin CLI argument parser and entry scaffold**
  - **Purpose:** Add the public CLI entry boundary without embedding solver or parsing logic directly in the CLI layer.
  - **Dependencies:** P15-T01, P1-T02.
  - **Completion criteria:** A thin CLI scaffold exists for case-path and basic run-option handling, and tests cover argument parsing and handoff to the application service boundary.

- [x] **P15-T04 — Implement CLI startup reporting behavior**
  - **Purpose:** Surface concise user-facing startup status and failure summaries for config and dependency-construction stages.
  - **Dependencies:** P15-T02, P15-T03, P1-T04.
  - **Completion criteria:** CLI startup reporting distinguishes input/configuration and startup dependency failures from later runtime phases, and tests cover representative user-facing failure outputs.

---

## Cross-Cycle Note

These implementation phases establish the earliest executable foundation layers only. Gas solving, droplet transport, breakup execution, outputs, plotting, and full validation execution should be added in later task phases after these runtime foundations are complete and verified.

---

## Phase 16. Quasi-1D Gas Solver Runtime

### Definition of Done

Phase 16 is done when the supported executable foundation path can compute an axial gas solution from validated case inputs, runtime geometry/grid objects, and the thermo abstraction, with explicit diagnostics and focused tests for gas-only behavior.

- [x] **P16-T01 — Create gas solver runtime module scaffold**
  - **Purpose:** Establish the concrete runtime module structure for gas-side helpers, solver execution, and diagnostics without embedding logic into unrelated layers.
  - **Dependencies:** P12-T02, P13-T05, P14-T04.
  - **Completion criteria:** Runtime gas-solver modules and exports exist with responsibilities aligned to the architecture, and tests cover basic import/wiring behavior.

- [x] **P16-T02 — Implement gas boundary-condition initialization for supported foundation cases**
  - **Purpose:** Convert validated inlet total conditions and outlet static pressure into the supported gas-side initialization path for the executable MVP foundation.
  - **Dependencies:** P16-T01, P5-T04, P14-T02.
  - **Completion criteria:** Boundary-condition initialization exists for the supported air foundation path, and tests cover representative valid and invalid boundary-condition handling.

- [x] **P16-T03 — Implement quasi-1D gas-state update utilities**
  - **Purpose:** Realize the runtime helper calculations needed to update gas-side axial state using geometry and thermo-provider queries.
  - **Dependencies:** P16-T01, P5-T03, P14-T01.
  - **Completion criteria:** Runtime helper calculations exist for supported gas-state updates and Mach/velocity-related state assembly, and tests cover representative consistency behavior.

- [x] **P16-T04 — Implement axial gas solver for supported executable cases**
  - **Purpose:** Build the gas-solver execution path that returns a structured `GasSolution` across the runtime axial grid.
  - **Dependencies:** P16-T02, P16-T03.
  - **Completion criteria:** A runtime gas solver returns structured axial gas results for supported air cases, and tests cover constant-area gas-only and converging/diverging sanity cases.

- [x] **P16-T05 — Implement gas diagnostics and failure propagation**
  - **Purpose:** Ensure gas-side nonphysical states and incomplete solution progression surface explicitly through the approved runtime error categories and diagnostics path.
  - **Dependencies:** P16-T04, P5-T05, P12-T04.
  - **Completion criteria:** Gas-solver runtime failures surface through explicit diagnostics/error behavior, and tests cover nonphysical-state and incomplete-progression cases.

---

## Phase 17. Droplet Transport Runtime

### Definition of Done

Phase 17 is done when the executable foundation path can initialize representative droplets, evaluate slip/drag against the gas solution, march droplet state along the grid, and surface focused diagnostics through structured droplet results.

- [x] **P17-T01 — Create droplet runtime module scaffold**
  - **Purpose:** Establish the concrete runtime module structure for drag models, droplet update helpers, transport solving, and diagnostics.
  - **Dependencies:** P12-T02, P16-T05.
  - **Completion criteria:** Runtime droplet modules and exports exist with responsibilities aligned to the architecture, and tests cover basic import/wiring behavior.

- [x] **P17-T02 — Implement standard-sphere drag model runtime path**
  - **Purpose:** Provide the MVP drag-model execution path behind a runtime abstraction rather than hard-wiring drag logic directly into transport code.
  - **Dependencies:** P17-T01, P6-T04.
  - **Completion criteria:** The supported drag model can evaluate representative drag inputs, and tests cover representative valid and invalid evaluation cases.

- [x] **P17-T03 — Implement droplet initialization and local update utilities**
  - **Purpose:** Realize runtime initialization and per-step droplet update helpers using gas-state lookup, slip evaluation, and drag inputs.
  - **Dependencies:** P17-T02, P6-T02, P6-T03.
  - **Completion criteria:** Runtime droplet initialization and local update helpers exist, and tests cover zero-slip and slip-driven update behavior.

- [x] **P17-T04 — Implement axial droplet transport solver**
  - **Purpose:** Build the runtime droplet marching path that returns a structured `DropletSolution` aligned to the gas solution and axial grid.
  - **Dependencies:** P17-T03, P6-T05.
  - **Completion criteria:** A runtime droplet solver returns structured axial droplet results for supported cases, and tests cover representative transport cases without breakup enabled.

- [x] **P17-T05 — Implement droplet diagnostics and failure propagation**
  - **Purpose:** Ensure unstable or nonphysical droplet states surface explicitly through runtime diagnostics rather than appearing later as ambiguous downstream failures.
  - **Dependencies:** P17-T04, P6-T06, P12-T04.
  - **Completion criteria:** Runtime droplet failures surface through explicit diagnostics/error behavior, and tests cover negative/invalid droplet metrics and inconsistent state cases.

---

## Phase 18. Breakup Runtime

### Definition of Done

Phase 18 is done when the runtime breakup interface exists, the MVP Weber-threshold model executes behind that interface, and breakup decisions are integrated into the droplet transport path with focused tests.

- [x] **P18-T01 — Create breakup runtime module scaffold and selector**
  - **Purpose:** Establish the concrete runtime structure for breakup-model interfaces, runtime selection, and future model extension.
  - **Dependencies:** P12-T02, P17-T05.
  - **Completion criteria:** Runtime breakup modules and exports exist with responsibilities aligned to the architecture, and tests cover basic import/wiring and selection behavior.

- [x] **P18-T02 — Implement runtime Weber number evaluation helper**
  - **Purpose:** Realize the runtime Weber number calculation path used by the MVP breakup decision.
  - **Dependencies:** P18-T01, P7-T02.
  - **Completion criteria:** Runtime Weber number evaluation exists with SI-consistent inputs/outputs, and tests cover representative no-breakup and breakup-driving values.

- [x] **P18-T03 — Implement critical-Weber breakup model runtime path**
  - **Purpose:** Provide the executable MVP breakup behavior behind the runtime breakup-model abstraction.
  - **Dependencies:** P18-T02, P7-T03.
  - **Completion criteria:** The runtime Weber-threshold breakup model returns structured `BreakupDecision` outputs, and tests cover threshold and non-threshold cases.

- [x] **P18-T04 — Integrate breakup execution into droplet transport runtime flow**
  - **Purpose:** Apply breakup decisions at the approved point in the droplet update sequence without hard-wiring breakup logic across unrelated modules.
  - **Dependencies:** P18-T03, P17-T04, P7-T05.
  - **Completion criteria:** Droplet transport integrates runtime breakup behavior in the approved sequence, and tests cover diameter updates and breakup-flag propagation.

- [x] **P18-T05 — Implement breakup diagnostics and runtime tests**
  - **Purpose:** Ensure breakup-trigger and no-trigger behavior remain explicit, testable, and protected against regressions.
  - **Dependencies:** P18-T04, P7-T06.
  - **Completion criteria:** Breakup-specific runtime diagnostics/tests exist for threshold, no-threshold, and invalid-parameter behavior.

---

## Phase 19. Result Assembly, Outputs, and Plotting Runtime

### Definition of Done

Phase 19 is done when runtime gas and droplet solutions can be assembled into structured simulation results, exported to CSV/JSON, and plotted through isolated output modules with focused tests.

- [x] **P19-T01 — Implement simulation-result assembly runtime path**
  - **Purpose:** Assemble structured simulation results, metadata, and diagnostics from gas and droplet runtime outputs without recomputing physics in IO layers.
  - **Dependencies:** P16-T05, P18-T05, P12-T03.
  - **Completion criteria:** A runtime result-assembly path exists for supported executable cases, and tests cover field presence and alignment between gas and droplet outputs.

- [x] **P19-T02 — Implement output-path and artifact-metadata helpers**
  - **Purpose:** Centralize runtime output-path conventions and artifact metadata creation before CSV/JSON/plot writers are added.
  - **Dependencies:** P19-T01, P1-T05.
  - **Completion criteria:** Runtime output-path and artifact-metadata helpers exist, and tests cover representative output-directory and artifact-name behavior.

- [x] **P19-T03 — Implement CSV writer runtime path**
  - **Purpose:** Write structured axial results to CSV through the IO layer only.
  - **Dependencies:** P19-T02, P8-T02.
  - **Completion criteria:** A runtime CSV writer serializes supported result fields in the documented format, and tests cover representative file content and error behavior.

- [x] **P19-T04 — Implement JSON writer runtime path**
  - **Purpose:** Write structured simulation results and metadata to JSON through the IO layer only.
  - **Dependencies:** P19-T02, P8-T03.
  - **Completion criteria:** A runtime JSON writer serializes supported result and metadata fields in the documented format, and tests cover representative content and error behavior.

- [x] **P19-T05 — Implement profile plotting runtime path**
  - **Purpose:** Generate the required MVP profile plots from structured results only, keeping figure logic separate from solver code.
  - **Dependencies:** P19-T01, P8-T04, P8-T05.
  - **Completion criteria:** Runtime plot generation produces the required MVP plot set from structured results, and tests cover representative plotting invocation and failure behavior.

---

## Phase 20. Validation Runtime

### Definition of Done

Phase 20 is done when runtime validation can consume structured simulation results, execute the approved sanity/trend checks, and return structured validation summaries without coupling validation logic to solver internals.

- [x] **P20-T01 — Create validation runtime module scaffold**
  - **Purpose:** Establish the concrete runtime structure for validation checks, reporting helpers, and future reference-case extension.
  - **Dependencies:** P12-T03, P19-T01.
  - **Completion criteria:** Runtime validation modules and exports exist with responsibilities aligned to the architecture, and tests cover basic import/wiring behavior.

- [x] **P20-T02 — Implement runtime sanity-check execution path**
  - **Purpose:** Realize the initial validation checks that consume structured results and test approved gas/droplet/breakup trend expectations.
  - **Dependencies:** P20-T01, P5-T06, P6-T07, P7-T06.
  - **Completion criteria:** Runtime validation checks exist for the documented sanity cases and trend expectations, and tests cover representative pass/fail outcomes.

- [x] **P20-T03 — Implement validation-report assembly runtime path**
  - **Purpose:** Return structured validation summaries suitable for application orchestration and later user-facing reporting.
  - **Dependencies:** P20-T02, P12-T03.
  - **Completion criteria:** A runtime validation-report path exists, and tests cover summary counts, observations, and status behavior.

- [x] **P20-T04 — Implement validation failure propagation behavior**
  - **Purpose:** Ensure validation execution problems remain distinguishable from solver, output, or startup failures.
  - **Dependencies:** P20-T03, P12-T04.
  - **Completion criteria:** Validation runtime failures surface through the approved error categories/diagnostics behavior, and tests cover representative validation-execution failure cases.

---

## Phase 21. Steam Runtime Enablement

### Definition of Done

Phase 21 is done when the thermo abstraction supports an executable steam path for the approved MVP subset, selection can resolve that path explicitly, and at least one steam-oriented runtime case is testable without breaking the air foundation path.

- [x] **P21-T01 — Implement runtime steam provider for the supported MVP subset**
  - **Purpose:** Add the first executable steam-provider path behind the existing thermo abstraction while preserving clean future IF97 replacement/extension.
  - **Dependencies:** P14-T04, P4-T03.
  - **Completion criteria:** A runtime steam provider exists for the supported equilibrium MVP subset, and tests cover representative valid and invalid steam-state behavior.

- [x] **P21-T02 — Extend thermo backend selection for supported steam cases**
  - **Purpose:** Resolve the executable steam provider through the configuration-driven selection path rather than special-casing steam in solver code.
  - **Dependencies:** P21-T01, P14-T03.
  - **Completion criteria:** Runtime thermo selection resolves supported steam cases and rejects unsupported steam backend names explicitly, with tests for positive and negative selection behavior.

- [x] **P21-T03 — Add steam runtime contract and integration tests**
  - **Purpose:** Protect the executable steam path and preserve swappability expectations for the thermo layer.
  - **Dependencies:** P21-T02, P4-T06.
  - **Completion criteria:** Runtime thermo tests cover the supported steam path at interface and integration levels, including at least one steam-oriented startup or gas-only execution case.

---

## Phase 22. Full MVP Application Execution

### Definition of Done

Phase 22 is done when the application and CLI can execute the supported MVP runtime workflow end-to-end, including gas solving, droplet transport with breakup, validation, CSV/JSON writing, plotting, and concise user-facing run reporting.

- [x] **P22-T01 — Extend application service to full simulation-run orchestration**
  - **Purpose:** Replace startup-only orchestration with the full runtime sequence while preserving the thin CLI boundary and modular application service design.
  - **Dependencies:** P16-T05, P18-T05, P19-T05, P20-T04.
  - **Completion criteria:** The application service can execute the supported full runtime workflow and return structured run status/results, with tests for representative success and failure paths.

- [x] **P22-T02 — Extend CLI from startup-only flow to full run flow**
  - **Purpose:** Make the CLI invoke the supported end-to-end application path while keeping argument parsing and user-facing reporting thin.
  - **Dependencies:** P22-T01, P15-T04.
  - **Completion criteria:** The CLI can trigger the supported full run path and report concise run status, with tests for representative CLI success and failure behavior.

- [x] **P22-T03 — Implement end-to-end air integration workflow test**
  - **Purpose:** Protect the first executable MVP path from YAML case input through generated runtime artifacts.
  - **Dependencies:** P22-T02, P19-T04.
  - **Completion criteria:** An end-to-end integration test exists for a supported air case from YAML input through structured outputs/artifacts.

- [x] **P22-T04 — Implement end-to-end steam-oriented integration workflow test**
  - **Purpose:** Confirm that the executable MVP workflow can run a supported steam-oriented case through the same application and CLI boundaries.
  - **Dependencies:** P21-T03, P22-T02.
  - **Completion criteria:** An end-to-end integration test exists for a supported steam-oriented case from YAML input through structured outputs/artifacts.

- [x] **P22-T05 — Reconcile examples and task-plan status with executable MVP behavior**
  - **Purpose:** Align example cases and task tracking with the implemented runtime workflow once the executable MVP path is in place.
  - **Dependencies:** P22-T03, P22-T04, P10-T01.
  - **Completion criteria:** Example-case coverage and task-plan status are updated to reflect the supported executable MVP workflow without introducing out-of-scope behavior.

---

## Phase 23. GUI Layer

### Definition of Done

Phase 23 is done when the GUI application can launch in a browser or desktop window, manage cases through the left panel, accept all simulation conditions through Pre tabs, invoke the solver through the Solve tab, and display axial profile plots and a results table through Post tabs, with the existing application service boundary fully preserved and focused tests covering the GUI-specific logic.

### Phase 23 Prerequisites

- Phase 22 must be complete.
- GUI technology selection must be documented and approved before any implementation task begins.
- `app/services.py` must not be modified as part of this phase.

---

- [x] **P23-T01 — Select and document GUI technology**
  - **Purpose:** Finalize the Python GUI framework before any module scaffolding begins, so all subsequent tasks use a consistent foundation.
  - **Dependencies:** P22-T05.
  - **Completion criteria:** The selected technology (e.g. Streamlit, Panel, Dash, or Tkinter) is documented with rationale, and any new runtime dependency is added to `pyproject.toml`. Technology constraints from [docs/architecture.md — Appendix B.7](architecture.md) are satisfied.
  - **Decision:** **Streamlit** selected. Rationale and candidate comparison documented in [docs/architecture.md — Appendix B.7.1](architecture.md). Dependency `streamlit==1.56.0` added to `pyproject.toml` via `uv add streamlit`.

- [x] **P23-T02 — Create GUI package scaffold and service bridge**
  - **Purpose:** Establish the `gui/` package structure and the `service_bridge.py` boundary that isolates all application service calls from GUI page logic.
  - **Dependencies:** P23-T01.
  - **Completion criteria:** The `gui/` package exists with the documented module layout; `service_bridge.py` wraps `ApplicationService`; tests cover import wiring and bridge call delegation.

- [x] **P23-T03 — Implement case store**
  - **Purpose:** Provide persistent case management (create, list, load, save) backed by a local YAML-backed case store in the `cases/` directory, using the existing config format.
  - **Dependencies:** P23-T02, P11-T06.
  - **Completion criteria:** `case_store.py` can create, list, load, and save cases; tests cover round-trip persistence and invalid-case handling.

- [x] **P23-T04 — Implement left panel — case management**
  - **Purpose:** Render the fixed left panel showing the case list, new-case creation, and open-case loading using the case store.
  - **Dependencies:** P23-T03.
  - **Completion criteria:** The left panel displays the case list, allows new case creation, and loads an existing case into GUI state; tests cover case selection and state update behavior.

- [x] **P23-T05 — Implement Pre Tab 1 — analysis conditions form**
  - **Purpose:** Provide form controls for all required simulation inputs (fluid, $T_0$, $P_0$, $P_2$, droplet injection, breakup parameters) with inline SI unit labels and validation.
  - **Dependencies:** P23-T04.
  - **Completion criteria:** All required condition fields are present with correct labels and validation; invalid inputs produce inline error messages; the form writes to GUI state correctly; tests cover field presence, validation behavior, and state updates.

- [x] **P23-T06 — Implement Pre Tab 2 — grid definition and area preview**
  - **Purpose:** Provide an editable $(x, A)$ table for area distribution input and a live area profile preview plot.
  - **Dependencies:** P23-T04.
  - **Completion criteria:** The grid table accepts tabulated area data; the preview plot updates when the table changes; nonpositive area values are rejected with inline errors; tests cover table editing and preview update behavior.

- [x] **P23-T07 — Implement Solve tab — run control and status display**
  - **MVP note:** The quasi-1D solver uses a spatial marching method, not an iterative convergence loop. Run status and completion indicators replace iterative convergence controls in the MVP GUI.
  - **Purpose:** Provide the Run button, solver status reporting, completion outcome, and user-readable diagnostics.
  - **Dependencies:** P23-T05, P23-T06.
  - **Completion criteria:** The Run button invokes the solver through `service_bridge.py` in a non-blocking manner; status and completion outcome are displayed; the Run button is disabled during execution; solver errors are reported in a user-readable format; tests cover run invocation, status update, and error reporting.

- [x] **P23-T08 — Implement Post Tab 1 — axial profile plots**
  - **Purpose:** Display the required axial profile plots from structured simulation results without recomputing physics in the GUI layer.
  - **Dependencies:** P23-T07.
  - **Completion criteria:** All required MVP profile plots are rendered from `SimulationResult` data; the user can select which quantities to display; plots update after each completed run; PNG export is available; tests cover plot rendering from a representative result object.

- [x] **P23-T09 — Implement Post Tab 2 — results table and CSV export**
  - **Purpose:** Display a scrollable tabular view of all axial result fields and allow CSV export.
  - **Dependencies:** P23-T07.
  - **Completion criteria:** The results table shows all axial fields for the completed run; CSV export produces a valid file; tests cover table population from a representative result object and export behavior.

- [x] **P23-T10 — Implement GUI application entry point and layout assembly**
  - **Purpose:** Assemble all panels and pages into the documented top-level layout and provide a launchable GUI entry point.
  - **Dependencies:** P23-T04 through P23-T09.
  - **Completion criteria:** The GUI launches from a single entry command; left panel and all tabs are reachable and functional; tests cover launch wiring and layout composition.

- [x] **P23-T11 — Add GUI launcher scripts**
  - **Purpose:** Provide `run20_gui.bat` and `run20_gui.sh` launcher scripts consistent with the existing helper script conventions.
  - **Dependencies:** P23-T10.
  - **Completion criteria:** Launcher scripts exist for Windows and POSIX, invoke the GUI entry point via `uv run`, and are documented in `README.md`.

- [x] **P23-T12 — Add GUI integration tests**
  - **Purpose:** Protect the GUI-to-service boundary and case store behavior against regressions.
  - **Dependencies:** P23-T10.
  - **Completion criteria:** Integration tests cover the full path from case load through solver invocation through result display for a representative air case, without requiring a live browser session.

---

## Phase 24. GUI Unit Settings

### Definition of Done

Phase 24 is done when the GUI has a configurable unit-settings page that applies user-selected display units to all Post tab outputs (plots and results table), unit conversion helpers are covered by focused tests, all SI boundaries are preserved in Pre tabs and solver layers, and the settings tab is integrated into the documented layout.

### Phase 24 Prerequisites

- Phase 23 must be complete.
- `app/services.py`, `domain/`, `solvers/`, `thermo/`, `io/`, `plotting/` must not be modified as part of this phase.

---

- [x] **P24-T01 — Update spec and architecture for unit settings**
  - **Purpose:** Add unit settings requirements to spec.md (B.11) and the unit conversion boundary rule to architecture.md (B.9) before any implementation begins.
  - **Dependencies:** P23-T12.
  - **Completion criteria:** spec.md B.11 and architecture.md B.9 are present with documented defaults, alternatives, and boundary rules.

- [x] **P24-T02 — Implement unit conversion module**
  - **Purpose:** Create `gui/unit_settings.py` with all unit-group definitions, conversion factors, and formatting helpers behind a clean testable boundary.
  - **Dependencies:** P24-T01.
  - **Completion criteria:** `gui/unit_settings.py` exists with `UNIT_GROUPS`, `DEFAULT_UNITS`, `FIELD_UNIT_GROUP`, `convert_value`, `convert_series`, `display_unit_label`, and `field_display_label`; tests cover representative conversion and formatting behavior.

- [x] **P24-T03 — Add unit preference fields to GUIState**
  - **Purpose:** Store per-group unit preferences as named fields in `GUIState` and expose them through a `unit_preferences()` helper.
  - **Dependencies:** P24-T02.
  - **Completion criteria:** `GUIState` has one `str` field per quantity group with documented defaults, and `unit_preferences()` returns a compatible dict; tests verify default values and mutation behavior.

- [x] **P24-T04 — Implement unit settings page**
  - **Purpose:** Provide a settings page with selectboxes for each unit group, calling only `gui/unit_settings.py` and `GUIState` helpers.
  - **Dependencies:** P24-T03.
  - **Completion criteria:** `gui/pages/unit_settings_page.py` exists with `get_unit_choices`, `apply_unit_preference`, `get_unit_preference`, and `render_unit_settings`; tests cover helper behavior without a Streamlit session.

- [x] **P24-T05 — Apply unit conversions in Post tab display**
  - **Purpose:** Update `post_graphs.py` and `post_table.py` to apply conversions from `state.unit_preferences()` while preserving backward compatibility when no preferences are provided.
  - **Dependencies:** P24-T04.
  - **Completion criteria:** `extract_plot_series` and `result_to_table_rows` accept an optional `unit_preferences` parameter; display values and labels reflect the selected units; all existing tests continue to pass.

- [x] **P24-T06 — Add unit settings tab to layout**
  - **Purpose:** Integrate the unit settings page into the documented top-level tab layout as a `⚙ Settings` tab.
  - **Dependencies:** P24-T04, P24-T05.
  - **Completion criteria:** The layout renders a Settings tab that calls `render_unit_settings()`; the existing tabs are unaffected.

- [x] **P24-T07 — Tests for unit conversion helpers and integration**
  - **Purpose:** Cover the unit conversion module, GUIState preference fields, page helpers, and the Post tab display helpers with unit preferences applied.
  - **Dependencies:** P24-T05, P24-T06.
  - **Completion criteria:** A focused test file covers all `gui/unit_settings.py` helpers, `GUIState` unit fields, `unit_settings_page.py` helpers, and `extract_plot_series` / `result_to_table_rows` with non-default unit preferences; all 117+ existing GUI tests continue to pass.

---

## Phase 25. FastAPI GUI Migration

### Definition of Done

Phase 25 is done when the FastAPI-based GUI can be launched from a separate script, provides the same case-management, condition-entry, simulation-run, result-display, and unit-setting capabilities as the earlier Phase 23/24 Streamlit prototype, and all existing tests (152+) continue to pass alongside new FastAPI-specific tests.

### Phase 25 Prerequisites

- Phase 24 must be complete.
- `app/services.py`, `domain/`, `solvers/`, `thermo/`, `io/`, `plotting/` must not be modified.
- `gui/case_store.py`, `gui/service_bridge.py`, `gui/unit_settings.py`, `gui/state.py`, `gui/pages/*.py` must not be structurally changed (additive changes only).
- The existing Streamlit entry point (`run20_gui.bat`) must continue to work.

---

- [x] **P25-T01 — Update SDD documents for FastAPI**
  - **Purpose:** Add FastAPI technology selection (B.7.2) to architecture.md and Phase 25 to tasks.md before any implementation begins.
  - **Dependencies:** P24-T07.
  - **Completion criteria:** architecture.md B.7.2 and tasks.md Phase 25 are present with documented rationale, module additions, and boundary rules.

- [x] **P25-T02 — Add FastAPI runtime dependencies**
  - **Purpose:** Add `fastapi`, `uvicorn[standard]`, `jinja2`, `python-multipart` to `pyproject.toml`; add `httpx` to dev dependencies for TestClient.
  - **Dependencies:** P25-T01.
  - **Completion criteria:** Dependencies are present in `pyproject.toml` and `uv sync` completes successfully.

- [x] **P25-T03 — Create core FastAPI modules**
  - **Purpose:** Create the FastAPI app factory, Pydantic schemas, job store, session store, plot utilities, and dependency-injection helpers.
  - **Dependencies:** P25-T02.
  - **Completion criteria:** `gui/fastapi_app.py`, `gui/schemas.py`, `gui/job_store.py`, `gui/session_store.py`, `gui/plot_utils.py`, and `gui/dependencies.py` exist and import cleanly.

- [x] **P25-T04 — Create REST API routers**
  - **Purpose:** Provide case CRUD, simulation run/status/result, and unit preference REST endpoints behind the service bridge boundary.
  - **Dependencies:** P25-T03.
  - **Completion criteria:** All five router modules exist; the FastAPI app mounts them; each endpoint returns the documented JSON shape.

- [x] **P25-T05 — Create HTML template and static assets**
  - **Purpose:** Provide a browser-based single-page interface served by FastAPI/Jinja2 with vanilla JavaScript for dynamic behavior.
  - **Dependencies:** P25-T04.
  - **Completion criteria:** `gui/templates/index.html`, `gui/static/app.css`, and `gui/static/app.js` exist; the page renders correctly in a browser; all tabs are navigable and the Run flow works end-to-end.

- [x] **P25-T06 — Create launcher scripts**
  - **Purpose:** Provide `run21_fastapi_gui.bat` and `run21_fastapi_gui.sh` consistent with existing script conventions.
  - **Dependencies:** P25-T05.
  - **Completion criteria:** Launcher scripts exist and are documented in README.md; the existing `run20_gui.bat` (Streamlit) is unaffected.

- [x] **P25-T07 — Add FastAPI tests and verify all tests pass**
  - **Purpose:** Protect the FastAPI API boundary and confirm no regressions in the existing 152 tests.
  - **Dependencies:** P25-T06.
  - **Completion criteria:** `tests/test_runtime_gui_fastapi.py` covers app creation, case CRUD, simulation status/result, and unit endpoints; all 152+ existing tests plus new FastAPI tests pass.

---


## Phase 25A. SDD Reconciliation

### Definition of Done

Phase 25A is done when the specification, architecture, and task plan use consistent terminology for the CLI MVP, the later GUI extension, FastAPI versus Streamlit roles, solve-tab behavior, case-store persistence, and copy-on-run execution semantics.

- [ ] **P25A-T01 — Align core MVP and GUI scope wording**
  - **Purpose:** Make the release story explicit across the SDD set by separating Core MVP, GUI extension, and later advanced study features.
  - **Dependencies:** P25-T07.
  - **Completion criteria:** `spec.md`, `architecture.md`, and `tasks.md` describe the CLI-focused MVP and later GUI layers without contradictory scope wording.

- [ ] **P25A-T02 — Standardize GUI framework terminology**
  - **Purpose:** Make FastAPI the current primary GUI architecture while preserving Streamlit as a legacy-compatible prototype/front-end path.
  - **Dependencies:** P25-T07.
  - **Completion criteria:** `architecture.md` clearly distinguishes FastAPI as primary/current and Streamlit as retained compatibility history.

- [ ] **P25A-T03 — Remove obsolete solve-tab convergence wording**
  - **Purpose:** Replace iterative convergence-control language with marching-solver run status, completion outcome, diagnostics, and user-readable error reporting.
  - **Dependencies:** P25-T07.
  - **Completion criteria:** `spec.md`, `architecture.md`, and relevant GUI task text no longer imply max-iteration or convergence-criterion controls for the marching solver.

- [ ] **P25A-T04 — Standardize case-store and run semantics**
  - **Purpose:** Use local YAML-backed case store terminology consistently and define copy-on-run semantics for in-flight jobs.
  - **Dependencies:** P25-T07.
  - **Completion criteria:** The SDD set uses one case-store term consistently and explicitly states that later case edits do not affect a running job.

- [ ] **P25A-T05 — Reconcile out-of-scope statements**
  - **Purpose:** Confirm that multi-case comparison and other non-MVP GUI features remain out of scope unless separately approved.
  - **Dependencies:** P25-T07.
  - **Completion criteria:** The SDD set contains no ambiguous claims that promote unsupported GUI features into the MVP or current GUI scope.

---

## Phase 26. Laval Nozzle Back-Pressure Sweep and Validation

### Definition of Done

Phase 26 is done when the simulator provides a CLI-accessible back-pressure sweep utility for Laval nozzles, generates $x$ vs $p/p_0$ validation plots and summary reports, and all outputs are compatible with downstream analysis and regression testing.

### Phase 26 Prerequisites

- Phase 22 must be complete.
- Phase 25 may remain available unchanged.
- External downstream jet structure, oblique shocks, and expansion fans remain out of scope.

---

- [x] **P26-T01 — Update SDD documents for Laval sweep/validation**
  - **Purpose:** Document the new CLI sweep command and automated p/p0 validation report in spec.md and tasks.md before implementation begins.
  - **Dependencies:** P25-T07.
  - **Completion criteria:** spec.md Appendix C and this phase document the sweep/validation scope, CLI interface, and validation artifact requirements.

- [x] **P26-T02 — Implement CLI sweep command**
  - **Purpose:** Add a CLI-accessible command/path to run the Laval nozzle back-pressure sweep utility without breaking the existing case-run workflow.
  - **Dependencies:** P26-T01.
  - **Completion criteria:** The CLI can invoke the sweep utility with a YAML case and a set/range of back pressures; all runs are executed and labeled outputs are generated.

- [x] **P26-T03 — Implement p/p0 validation report**
  - **Purpose:** Add automated p/p0-specific validation report generation for the sweep outputs and integrate it into the sweep workflow.
  - **Dependencies:** P26-T02.
  - **Completion criteria:** The utility produces a combined $x$ vs $p/p_0$ plot, summary CSV/JSON, and a validation report for all sweep cases.

- [x] **P26-T04 — Test and verify sweep/validation features**
  - **Purpose:** Add or update tests for the new CLI command and validation report, run focused regression tests, and confirm artifacts are generated.
  - **Dependencies:** P26-T03.
  - **Completion criteria:** Tests cover CLI sweep invocation, output artifact generation, and validation report content; all tests pass.

---

## Phase 27. GUI Multi-Value Conditions Sweep and Overlay

### Definition of Done

Phase 27 is done when the FastAPI GUI accepts comma/space-separated multi-value numeric condition inputs, expands them into immutable per-run payloads at Solve time, overlays the resulting runs in the Graphs tab, aggregates them in the results table/CSV export, and the SDD plus focused tests are updated accordingly.

### Phase 27 Prerequisites

- Phase 25 must be complete.
- Phase 25A may be updated as part of this phase where terminology needs to be reconciled.
- The case store must remain YAML-compatible with the single-case runtime schema.

---

- [x] **P27-T01 — Update SDD for GUI multi-value Conditions sweeps**
  - **Purpose:** Document multi-value numeric Conditions input, solve-time sweep expansion, overlay graphs, and aggregated results behavior before implementation.
  - **Dependencies:** P25-T07.
  - **Completion criteria:** `spec.md`, `architecture.md`, and `tasks.md` describe the behavior and preserve the case-store/copy-on-run boundaries.

- [x] **P27-T02 — Implement GUI-side numeric token parsing and sweep expansion**
  - **Purpose:** Add a GUI-layer helper that parses comma/space-separated SI numeric tokens, validates them, and expands them into immutable single-run payloads.
  - **Dependencies:** P27-T01.
  - **Completion criteria:** Multi-value parsing is reusable and tested; malformed tokens and excessive Cartesian-product expansions are rejected with clear errors.

- [x] **P27-T03 — Extend FastAPI Solve flow for multi-run execution**
  - **Purpose:** Let the FastAPI `/api/simulation/run` flow accept a UI snapshot, expand multi-value Conditions inputs, and execute one solver run per expanded payload without changing solver internals.
  - **Dependencies:** P27-T02.
  - **Completion criteria:** The run endpoint preserves copy-on-run semantics, uses immutable per-run snapshots, and returns aggregated job results for completed sweeps.

- [x] **P27-T04 — Implement overlay Graphs and aggregated Table/CSV display**
  - **Purpose:** Use structured per-run `SimulationResult` objects to overlay plots with legends and aggregate results rows with run labels.
  - **Dependencies:** P27-T03.
  - **Completion criteria:** The Graphs tab overlays runs on shared axes, the Table tab includes run labels, and CSV export includes aggregated rows.

- [x] **P27-T05 — Add focused tests and verify regression safety**
  - **Purpose:** Protect numeric parsing, sweep expansion, FastAPI job execution, overlay plot generation, and aggregated table behavior.
  - **Dependencies:** P27-T04.
  - **Completion criteria:** New focused tests pass alongside the existing suite, including a full `pytest` run.
