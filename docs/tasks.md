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
  - **Completion criteria:** Required plots are documented for pressure, temperature, working-fluid velocity, droplet velocity, Mach number, droplet mean diameter, droplet maximum diameter, and Weber number.

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
