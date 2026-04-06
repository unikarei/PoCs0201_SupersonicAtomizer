#-------------------------------------------------------------------------#
1) まず最初に入れる「親プロンプト」
#-------------------------------------------------------------------------#

You are my specification-driven development assistant for GitHub Copilot in VSCode.

Your role is to help me build a Python-based engineering simulator using strict SDD workflow.
Do not jump directly into implementation.
Do not generate large code first.
Always work in this order:

1. spec
2. architecture
3. tasks
4. copilot-instructions
5. implementation

Project goal:
Build a Python simulator for atomization of water droplets in a quasi-1D compressible flow duct/nozzle.
Working fluid is air or steam.
Steam thermodynamic properties should support IF97-based handling.
The simulator must predict how droplets are accelerated and broken up by the working fluid.

Core simulation scope:
- Quasi-1D compressible flow along x-axis
- Inputs:
  - inlet total pressure
  - inlet total temperature
  - outlet static pressure
  - inlet wetness (optional / mainly for steam)
  - area distribution along x-axis
  - thermodynamic property model: air or steam(IF97)
  - equilibrium steam assumption for first version
  - droplet injection conditions
- Outputs along x-axis:
  - working fluid velocity
  - droplet velocity
  - droplet mean diameter
  - droplet maximum diameter
  - Weber number
  - pressure
  - temperature
  - Mach number
- Visualization:
  - plot all major values against x-axis
- First version should be research-oriented, modular, testable, and easy to extend.

Development constraints:
- Python only
- Target environment: VSCode
- Must be structured for maintainability and future extension
- Numerical robustness is more important than feature count
- Start with MVP, then define extensions
- Keep units in SI
- Separate physics, solver, IO, plotting, validation, and config layers
- Explicitly list assumptions, limitations, and validation strategy

Required deliverables:
- docs/spec.md
- docs/architecture.md
- docs/tasks.md
- .github/copilot-instructions.md

Important behavior rules:
- Before writing each file, summarize what you are going to write
- If any requirement is ambiguous, do not invent silently; create an “Open Questions / Assumptions” section
- Prefer simple, extensible models for MVP
- Keep the first implementation focused on quasi-1D internal flow and droplet breakup
- Treat external free jet / impingement as future extension unless explicitly included in the approved spec
- Use clear markdown headings and checklists
- Do not write code until tasks are approved

Now start by drafting docs/spec.md only.

#-------------------------------------------------------------------------#
2) spec.md を作らせるプロンプト
#-------------------------------------------------------------------------#

これは親プロンプトの後に入れるやつです。

Create docs/spec.md for this project.

The document must include:

1. Purpose
2. Scope
3. Out of scope
4. Users and use cases
5. Functional requirements
6. Non-functional requirements
7. Inputs
8. Outputs
9. Physics assumptions
10. Numerical assumptions
11. Validation requirements
12. Error handling requirements
13. Constraints
14. Open questions
15. Acceptance criteria

Project specifics to reflect:
- Simulator for droplet atomization in quasi-1D duct/nozzle flow
- Working fluid: air or steam
- Steam properties: IF97-based support planned
- Equilibrium steam assumption for first release
- User provides area distribution A(x)
- User provides inlet total pressure, inlet total temperature, outlet static pressure, and optional inlet wetness
- User provides droplet injection conditions
- Simulator calculates working fluid velocity, droplet velocity, droplet diameter evolution including maximum droplet size, and related indicators such as Weber number
- Results are plotted versus x-axis

MVP requirements:
- Quasi-1D gas solver
- Droplet transport with slip velocity
- Simple breakup criterion based on Weber number threshold
- CSV/JSON outputs
- Matplotlib plotting
- YAML input file
- CLI execution

Be explicit about what the MVP will NOT solve yet:
- 3D CFD
- droplet-droplet collision/coalescence
- wall-film physics
- detailed free jet external field
- plate impingement
- non-equilibrium condensation
- high-fidelity turbulence modeling

Write the spec in a form suitable for engineering software development.

#-------------------------------------------------------------------------#
3) architecture.md を作らせるプロンプト
#-------------------------------------------------------------------------#

ここがかなり重要です。
Copilot はここでモジュール分割を先に決めると暴走しにくいです。

Now create docs/architecture.md based on the approved spec.

The architecture document must include:

1. System overview
2. Design principles
3. Module decomposition
4. Data flow
5. Main domain models
6. Solver flow
7. File and package structure
8. Interfaces between modules
9. Configuration strategy
10. Error handling strategy
11. Logging strategy
12. Testing strategy
13. Validation strategy
14. Extension strategy
15. Technical risks

Design goals:
- clean modular Python architecture
- physics and numerics separated
- easy future extension from air-only to steam(IF97)
- easy future extension from simple breakup to advanced breakup models
- testability first
- clear boundaries between config, physics, solvers, plotting, IO, and application layer

Recommended modules to consider:
- config
- domain
- thermo
- geometry
- grid
- gas_solver
- droplet_solver
- breakup_model
- evaporation_model
- coupling
- simulation_runner
- io
- plotting
- validation
- cli

Please propose a concrete directory structure such as:
- src/...
- tests/...
- examples/...
- docs/...

Also define the main data classes, for example:
- SimulationConfig
- GeometryProfile
- GasState
- DropletState
- SimulationResult

For the solver flow, explicitly show:
input -> preprocess -> gas solve -> droplet update -> breakup evaluation -> output -> plotting

Do not write implementation code. Only architecture and interfaces.

#-------------------------------------------------------------------------#
4) tasks.md を作らせるプロンプト
#-------------------------------------------------------------------------#

ここは 依存関係つきのチェックリスト にするのが一番使いやすいです。

Now create docs/tasks.md based on the approved spec and architecture.

Requirements for tasks.md:
- Use phased implementation
- Use markdown checklist format
- Break work into small, testable tasks
- Each task should have:
  - task ID
  - title
  - purpose
  - dependencies
  - completion criteria
- Order tasks so that GitHub Copilot can implement them incrementally without confusion

Please structure tasks in these phases:

Phase 1: Project bootstrap
- repository structure
- pyproject or requirements
- lint/test setup
- base CLI
- config schema

Phase 2: Core domain and config
- data models
- YAML loading
- validation of inputs
- units and constants

Phase 3: Geometry and grid
- x-grid generation
- area interpolation
- geometry validation

Phase 4: Thermodynamics
- air ideal gas model
- steam interface abstraction
- placeholder IF97 adapter

Phase 5: Quasi-1D gas solver
- state update logic
- Mach/pressure/temperature/velocity outputs
- boundary condition handling

Phase 6: Droplet solver
- droplet state transport
- slip velocity
- drag
- droplet Reynolds number
- Weber number

Phase 7: Breakup model
- critical Weber model
- mean diameter update
- maximum diameter update
- breakup event tracking

Phase 8: Output and plotting
- CSV/JSON export
- x-axis plots
- run summary

Phase 9: Tests
- unit tests
- integration tests
- regression tests

Phase 10: Documentation and examples
- sample YAML cases
- user quickstart
- limitations

Include explicit “Definition of Done” for each phase.
Do not write code yet.

#-------------------------------------------------------------------------#
5) .github/copilot-instructions.md を作らせるプロンプト
#-------------------------------------------------------------------------#

これは Copilot を毎回ぶらさないためのファイルです。

Now create .github/copilot-instructions.md for this repository.

The file should instruct GitHub Copilot how to behave when generating code in this project.

Include these rules:

- Follow SDD strictly:
  - spec first
  - architecture second
  - tasks third
  - implementation last
- Never bypass the approved spec
- Do not introduce large unapproved features
- Prefer small incremental commits
- Always preserve modular boundaries
- Keep SI units everywhere
- Prefer explicit dataclasses / typed models
- Write docstrings for public functions and classes
- Add tests for all non-trivial logic
- Avoid hidden assumptions
- If something is ambiguous, add a TODO or ask for clarification in comments
- Do not hardcode magic numbers without named constants
- Keep plotting separate from physics
- Keep thermodynamic model abstraction clean so air and steam can be swapped
- Keep breakup model pluggable
- Avoid premature optimization
- Prefer readability and validation over cleverness
- Use Python type hints
- Use pathlib, dataclasses, typing, and clear module imports
- Keep functions short and focused
- Validate numerical inputs defensively
- Fail loudly on invalid physics inputs

Also include project-specific coding conventions:
- package under src/
- tests under tests/
- YAML examples under examples/
- docs under docs/
- use matplotlib for plots
- use pytest for tests
- use pydantic or dataclasses for config validation, but be consistent
- all outputs should be reproducible from one config file

Make the tone direct and operational for Copilot.

#-------------------------------------------------------------------------#
6) 最後に実装開始させるプロンプト
#-------------------------------------------------------------------------#

仕様書群ができた後、これで初めて実装へ進ませます。

Now begin implementation strictly following:
- docs/spec.md
- docs/architecture.md
- docs/tasks.md
- .github/copilot-instructions.md

Implementation rules:
- implement only the earliest incomplete task from docs/tasks.md
- before coding, restate the task and its completion criteria
- create only the minimum code necessary for that task
- after coding, summarize what was added
- list any assumptions made
- do not implement future tasks early
- do not refactor unrelated files
- add or update tests for the task
- stop after completing that one task

Start with Phase 1, Task 1.

#-------------------------------------------------------------------------#
7) かなり大事な運用ルール
#-------------------------------------------------------------------------#

実務的には、Copilot に毎回これも言った方がいいです。

追加の短い運用プロンプト
Use the SDD files as the single source of truth.
If implementation conflicts with spec or architecture, stop and report the conflict instead of guessing.
仕様変更時のプロンプト
A new requirement has been added.
Do not edit code first.
First update spec.md, then architecture.md if needed, then tasks.md, and only after that propose code changes.
暴走防止プロンプト
Do not generate placeholder-heavy code across the whole repository.
Implement only one task at a time with working code and tests.

#-------------------------------------------------------------------------#
8) 一番おすすめの実際の流し方
#-------------------------------------------------------------------------#

VSCode の Copilot Chat では、順番はこうです。

親プロンプト
spec生成
specをレビュー
architecture生成
architectureをレビュー
tasks生成
copilot-instructions生成
実装開始プロンプト
1タスクずつ進める

#-------------------------------------------------------------------------#
9) あなたの案件向けに一言でいうと
#-------------------------------------------------------------------------#

この案件では、Copilot に最初から
「自由噴流・衝突板・凝縮・IF97・液滴破砕を全部実装せよ」
とやるとかなり崩れます。

なので最初はこう固定した方がいいです。

MVP: quasi-1D 内部流れ + droplet transport + simple Weber breakup
Phase 2: steam IF97
Phase 3: evaporation / equilibrium steam
Phase 4: free jet / impingement extension

この切り方が一番安定です。