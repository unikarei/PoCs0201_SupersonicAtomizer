# Supersonic Atomizer Simulator Specification

## 1. Purpose

This document defines product-level requirements for the Supersonic Atomizer Simulator.
It is the normative source for product scope, expected behavior, and acceptance boundaries.

This specification is intentionally concise and requirement-focused.
Detailed algorithm notes, rationale, and design alternatives belong to architecture and topic-specific documents under `docs/`.

## 2. Document Roles and Priority

Requirement and implementation planning shall follow this order:

1. `docs/spec.md` (product requirements and scope)
2. `docs/architecture.md` (module boundaries and implementation design)
3. `docs/tasks.md` (phase/task execution plan)

When statements conflict, this specification has priority over architecture and tasks.

## 3. Product Scope

### 3.1 MVP Scope

The MVP shall provide:

- steady quasi-1D internal compressible flow along axial coordinate `x`
- user-defined area profile `A(x)`
- working-fluid support for air and steam through a thermo abstraction
- representative droplet transport with slip-based acceleration
- configuration-driven breakup behavior (default Weber-threshold model)
- YAML-driven case input
- CLI execution
- CSV/JSON outputs
- Matplotlib static plotting

### 3.2 Approved Extension Scope

Beyond the CLI MVP, the project includes an approved browser GUI extension that wraps the same application-service boundary.
The GUI is an orchestration and presentation layer only; it must not introduce solver-side physics logic.

### 3.3 Out of Scope

The following remain out of scope unless explicitly re-approved:

- 2D/3D CFD and turbulence-resolving multiphase simulation
- droplet collision/coalescence
- wall-film and wall-interaction physics
- external free-jet and impingement modeling
- non-equilibrium condensation
- solver-side optimization automation that bypasses documented validation workflow

## 4. Functional Requirements

### 4.1 Inputs and Case Definition

The simulator shall:

- accept YAML case input and validate schema plus semantic constraints
- require SI units for solver inputs and internal computation
- accept tabulated axial area profile input
- support working-fluid selection (`air`, `steam`)
- support droplet-related inputs needed by selected injection and breakup models
- support configuration-driven model selection (thermo backend, drag model, breakup model, coupling mode)

### 4.2 Gas-Phase Solver Behavior

The simulator shall:

- solve a steady quasi-1D compressible internal-flow problem on an axial grid
- compute axial profiles including pressure, temperature, density, gas velocity, and Mach number
- support converging-diverging Laval nozzle branch handling for approved case families
- support one fitted internal normal shock in approved Laval-nozzle handling
- keep thermo calculations behind a swappable provider interface
- support explicit backend selection for steam providers when available

### 4.3 Droplet Transport and Breakup Behavior

The simulator shall:

- compute droplet velocity, representative diameters, slip velocity, and Weber number along `x`
- support configuration-driven breakup model selection
- support Weber-threshold breakup as baseline behavior
- support KH-RT and bag-stripping models through the same breakup boundary
- evaluate breakup and drag behavior using explicit model inputs and diagnostics
- expose droplet-side coupling source summaries required by approximate two-way coupling

### 4.4 Injection Mode Behavior

The simulator shall support `injection_mode` with at least:

- `droplet_injection`: inlet provides already-formed droplets; no primary atomization step
- `liquid_jet_injection`: inlet provides liquid-jet properties and a configurable primary-breakup correlation

For `liquid_jet_injection`, the solver shall:

- compute and report primary-breakup diagnostics (including breakup length)
- transition to droplet transport after breakup according to configured initial-size model
- surface model-validity warnings for out-of-range empirical conditions

### 4.5 Coupling Behavior

The simulator shall support configuration-driven coupling mode selection:

- `one_way`: gas-to-droplet only
- `two_way_approx`: bounded operator-split reduced-order feedback loop

When `two_way_approx` is selected, the simulator shall expose convergence-related diagnostics and enforce bounded iteration controls.

### 4.6 Outputs, Artifacts, and Plotting

The simulator shall:

- export primary results to CSV and JSON
- generate Matplotlib plots of major axial quantities
- provide run metadata and diagnostics suitable for CLI and GUI display
- manage output artifacts under case-oriented directories

Output artifact behavior shall include:

- per-run artifacts under `outputs/<project>/<case>/<run-id>/`
- case-level overlay artifacts under `outputs/<project>/<case>/plots/`
- explicit cleanup policy for solve execution
- default pre-run case cleanup enabled (`clean_case: true`) unless explicitly disabled

### 4.7 GUI Functional Requirements

The browser GUI extension shall provide:

- project/case explorer with case-store-backed CRUD and move/rename flows
- analysis-condition and grid-definition workflows
- solve execution monitoring with non-blocking status and result retrieval
- post-run graphs, table, and report views sourced from structured result payloads
- multi-value condition expansion into parameter sweeps at GUI/application orchestration boundary

Graph and grid consistency requirements:

- `Area Profile` shall be available in post-run graph generation and default ordering
- grid view shall include an explicit `x` vs `Area` figure from current tabulated area data
- multi-run overlays shall be generated and persisted using the same data path as graph display behavior

### 4.8 Chat Requirements (GUI)

The GUI chat subsystem shall:

- provide a right-side resizable conversational panel
- bind context to current selection scope (`case` or `project`)
- include selected-case/project context and latest available run summary in prompt assembly
- route LLM invocation through a server-side boundary (no browser credential exposure)
- degrade gracefully when no LLM backend is configured
- persist chat history as JSON using scope-aware paths
  - case scope: `cases/<project>/chat/<case>/`
  - project scope: `cases/<project>/chat/`

Reasoning and image-handling policy shall include:

- allow domain common knowledge discussion
- prohibit unsupported speculation
- require computational verification for quantitative predictions before returning numeric conclusions
- include an inventory of available graph images in context
- attach binary image data only when explicitly requested

### 4.9 Chat-Driven Conditions/Grid Change Patterns

The chat subsystem shall support the following implementation patterns for
editing analysis conditions and grid definitions:

1. Advisory-only pattern
  - Chat returns guidance text only.
  - No mutable configuration payload is generated.

2. Draft-patch proposal pattern
  - Chat returns a structured proposal payload containing candidate
    Conditions/Grid edits.
  - No persistence side effect occurs.

3. Form-prefill proposal pattern
  - Chat returns structured values that the GUI can map to form fields.
  - User still edits fields manually and uses existing save actions.

4. Approval-gated transactional update pattern (MVP primary path)
  - Chat creates proposals only.
  - User explicit approval is required before any update attempt.
  - A dedicated API updates Conditions/Grid fields.
  - Existing validation chain is mandatory before persistence.
  - UI displays structured change diff and requires final confirmation.

5. Batch proposal pattern
  - Chat can stage multiple proposal units in one request.
  - Batch apply is still approval-gated and validation-gated.

Pattern 4 shall be treated as the default production path for mutable
chat-driven updates in the MVP.

## 5. Non-Functional Requirements

The system shall prioritize:

- modularity and clear separation of concerns
- numerical robustness and explicit failure signaling
- maintainability and extension readiness over premature complexity
- deterministic, automatable testing for non-trivial logic
- SI-unit consistency end-to-end

## 6. Constraints

The project constraints are:

- Python-only implementation
- solver logic isolated from GUI, plotting, and raw YAML parsing concerns
- plotting and serialization layers must not recompute physics
- thermodynamic backends must remain abstraction-driven and swappable
- breakup behavior must remain pluggable and configuration-driven

## 7. Validation and Acceptance

### 7.1 Validation Requirements

Validation shall cover at minimum:

- gas-only sanity cases
- geometry/profile sanity cases
- droplet transport and breakup-trigger behavior cases
- steam-path coverage through thermo abstraction
- selected Laval nozzle back-pressure families for trend checks

### 7.2 Quantitative Workflow Requirements

The project shall support:

- validation-campaign reporting against documented references
- one-at-a-time sensitivity analysis on selected parameters
- bounded candidate optimization workflows
- uncertainty summary reporting for objective values

### 7.3 Acceptance Boundaries

Product acceptance requires:

- YAML-to-result execution for approved scope
- correct boundary/module separation per architecture
- explicit handling/reporting of invalid input and numerical failure
- output formats and artifact behavior consistent with this specification

## 8. Traceability to Detailed Documents

This file is the compact requirement baseline.
Detailed definitions remain in dedicated documents under `docs/` (for example thermo, breakup, grid, validation, GUI, and export-format documents).

`docs/tasks.md` shall map implementation tasks to requirements defined here.

## 9. Revision Policy

When requirements change:

1. update this specification first
2. align architecture boundaries and data flow second
3. align tasks and phase execution plan third

No implementation shall silently diverge from this order.
