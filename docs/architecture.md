# Supersonic Atomizer Simulator Architecture

## 1. Purpose and Relationship to Specification

This document defines implementation architecture for requirements in `docs/spec.md`.

Role separation:

- `docs/spec.md`: product-level requirements and acceptance boundaries
- `docs/architecture.md`: module boundaries, contracts, data flow, and engineering rules
- `docs/tasks.md`: phased execution plan

This architecture is intentionally boundary-driven and implementation-oriented.

## 2. Architectural Principles

### 2.1 Layer Separation

The system is organized into separable concerns:

- configuration and validation
- domain models
- thermo providers
- geometry and grid
- gas solver
- droplet solver
- breakup models
- IO and plotting
- validation/reporting
- application orchestration
- CLI and GUI frontends

### 2.2 Interface-First Dependencies

Core solvers depend on interfaces, not concrete implementations, especially for:

- thermo providers
- breakup models
- drag behavior

### 2.3 Explicit Data Contracts

Cross-layer communication uses typed models and structured payloads.
Raw YAML and browser payloads are translated at boundaries and do not leak into solver internals.

### 2.4 Robustness and Auditability

The system prioritizes stable, explicit behavior over hidden fallback.
Errors and warnings are categorized and surfaced with context.

## 3. Runtime Views

### 3.1 CLI Runtime View

1. CLI resolves case path and runtime options.
2. Config layer parses and validates YAML.
3. Translator builds typed case model.
4. Geometry/grid and model providers are instantiated.
5. Gas and droplet pipelines execute (with optional bounded two-way loop).
6. Result assembly produces structured outputs.
7. IO/plotting write artifacts.
8. Validation/reporting modules summarize outcomes.

### 3.2 GUI Runtime View

1. Browser UI edits and stores case-scoped conditions through API routes.
2. Solve request creates immutable run snapshot payload(s).
3. Background job executes one single-case payload per expanded sweep run.
4. Job store provides status and completed results for polling.
5. Graph/table/report/chat views are assembled from structured results and stored artifacts.

GUI remains an orchestration/presentation layer and does not execute solver logic directly.

## 4. Module Boundaries and Responsibilities

### 4.1 Core Simulation Layers

- Config: parse YAML, apply defaults, perform schema/semantic validation, translate to typed config models
- Domain: shared case/state/result contracts
- Thermo: provider interface plus concrete air/steam backends
- Geometry/Grid: area profile representation and axial discretization
- Gas Solver: quasi-1D gas-state evolution, branch handling, diagnostics
- Droplet Solver: transport, drag/slip update, breakup invocation, coupling-source summaries
- Breakup: pluggable breakup interface and model registry (`weber_critical`, `khrt`, `bag_stripping`)
- IO: output path policy, CSV/JSON serialization, metadata
- Plotting: figure generation from result models only
- Validation: case checks, trend/metric evaluation, reporting
- App Orchestration: end-to-end sequencing and cross-layer coordination

### 4.2 Frontend and Service Layers

- CLI: thin command entrypoint and result/error presentation
- GUI FastAPI app: routes, templates/static, session/job orchestration
- GUI case store: project/case persistence boundary
- GUI service bridge: sole gateway from GUI actions to application service
- GUI chat service/router: scope-aware prompt assembly and provider integration

## 5. Key Interface Contracts

### 5.1 Thermo Contract

Gas solver consumes thermo through a provider interface.
Concrete steam/air formulas must not be hard-wired into gas solver logic.
Backend selection remains configuration-driven.

### 5.2 Breakup Contract

Droplet solver calls breakup through a model interface that returns a structured decision.
Breakup models are stateless at cell-local evaluation level and do not access raw YAML or solver internals directly.

### 5.3 Coupling Contract

Droplet transport exposes source summaries.
Application orchestration applies optional bounded reduced-order feedback for `two_way_approx` without violating gas solver boundary.

### 5.4 Injection Contract

Droplet layer supports `droplet_injection` and `liquid_jet_injection`.
Primary-breakup correlation logic (for liquid-jet mode) stays in droplet-layer helper components and returns explicit diagnostics.

### 5.5 IO/Plotting Contract

IO and plotting consume result models only.
They must not recompute physics or re-run solver calculations.

## 6. Data and Persistence Boundaries

### 6.1 Case Data

- canonical case store: `cases/<project>/<case>.yaml`
- legacy flat case compatibility handled at case-store/router boundary

### 6.2 Run Artifacts

- per-run: `outputs/<project>/<case>/<run-id>/...`
- case overlays: `outputs/<project>/<case>/plots/*_overlay.png`
- cleanup policy is config-driven; default behavior cleans prior case outputs before a new solve

### 6.3 Chat Data

Chat history is JSON sidecar data, not embedded in case YAML.

- case scope: `cases/<project>/chat/<case>/`
- project scope: `cases/<project>/chat/`

### 6.4 Session and Job State

GUI transient runtime state (active job ids, UI selections, sidebar widths, etc.) is session-local and separated from canonical case/run persistence.

## 7. Error and Diagnostic Architecture

Error categories:

- input/schema/semantic configuration errors
- unsupported model/backend selection errors
- thermo-state errors
- numerical solver errors
- output/persistence errors
- validation/reporting errors
- GUI integration/provider errors

Propagation rules:

- low-level modules raise specific errors
- orchestration enriches with case/run context
- CLI/GUI surfaces concise user-facing messages

No silent fallback for unsupported model names, invalid states, or unavailable configured backends.

## 8. Validation and Testing Architecture

### 8.1 Testing Layers

- unit tests: isolated model and utility logic
- contract tests: thermo/breakup/drag pluggable interfaces
- integration tests: YAML-to-result and GUI API workflows
- regression tests: stable reference behavior and artifact contracts

### 8.2 Validation Layers

- solver sanity validation
- physics-trend validation
- reference-case validation and reporting

### 8.3 Quantitative Improvement Workflows

Architecture supports validation reporting, sensitivity analysis, bounded optimization, and uncertainty summarization as modular validation concerns separated from solver core.

## 9. GUI Architecture Constraints

- GUI modules do not import solver internals directly
- GUI invokes application service through a documented bridge/router boundary
- multi-value sweep expansion is GUI/application orchestration logic only
- report generation reuses existing structured result payloads
- overlay generation uses the same graph-data extraction path as interactive graph rendering
- chat prompts include scope metadata and reasoning guardrails
- graph-image inventory may be provided to the LLM; binary image payloads are attached only when explicitly requested
- provider credentials remain server-side and are never exposed to browser JavaScript

### 9.1 Chat-Driven Conditions/Grid Change Architecture

Five patterns are supported at the architecture level:

1. advisory-only
2. draft-patch proposal
3. form-prefill proposal
4. approval-gated transactional update
5. batch proposal

For mutable flows, Pattern 4 is the baseline boundary contract.

Pattern 4 required sequence:

1. Chat layer emits a proposal object only; no direct persistence.
2. GUI requires explicit user approval and calls dedicated proposal-apply API.
3. API applies proposal over current case config using Conditions/Grid-limited patch scope.
4. Existing validation chain is executed before persistence:
	- schema validation
	- semantic validation
	- default application
	- translation/runtime-ready checks
5. API returns structured before/after diff payload.
6. GUI shows diff and executes final confirmation API.

Boundary rules:

- Chat service must not write case YAML directly.
- Proposal lifecycle state (proposed/applied/confirmed/rejected) remains in GUI/API layer.
- Validation logic remains in existing config/application validation modules.
- Case persistence remains through `CaseStore` boundary.

## 10. Extension Strategy

The architecture is designed for additive extension through stable contracts:

- thermo backend replacement/addition (including IF97-ready paths)
- breakup model expansion
- drag model improvements
- stronger coupling strategies
- richer validation datasets and reports
- GUI feature growth without solver-layer modification

## 11. Governance and Change Order

When architecture changes are required:

1. align or update `docs/spec.md` first if requirements changed
2. update this architecture document second
3. update `docs/tasks.md` third
4. execute implementation in small, traceable task units

No broad implementation should proceed when this order is violated.

## 12. Mapping to Detailed Design Documents

This file is the compact architecture baseline.
Detailed design notes and deep-dives are maintained in topic-specific documents under `docs/` (thermo, breakup, drag, grid, validation, GUI, export schema, and error taxonomy).

Those detailed documents shall remain consistent with boundaries defined here.
