# Supersonic Atomizer Simulator

Quasi-1D compressible internal flow + droplet transport + Weber-threshold breakup simulator for engineering research.

---

## Quick Start

### 1. Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package & project manager

```bash
# Install uv (if not already installed)
# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone & Setup

```bash
git clone <repository-url>
cd 0201_SupersonicAtmizer
```

After cloning, choose one of the following workflows.

### 3A. Standard `uv` Commands

#### Setup

```bash
uv sync
```

`uv sync` creates `.venv`, installs runtime dependencies (PyYAML, matplotlib) and dev dependencies (pytest), and installs the project itself in editable mode.

#### Run a Simulation

```bash
# Air nozzle case
uv run supersonic-atomizer examples/air_nozzle.yaml

# Steam nozzle case
uv run supersonic-atomizer examples/steam_nozzle.yaml
```

#### Run the Laval-Nozzle Sweep

```bash
uv run supersonic-atomizer laval-sweep examples/laval_nozzle_air.yaml
```

This command generates:

- an internal-flow textbook comparison plot for $x$ vs $p/p_0$,
- a sweep summary JSON file,
- an automated Markdown validation report for the `b`, `d`, `g`, `h`, `j`, and `k` internal regimes.

> `uv run` automatically uses the project's virtual environment — no manual activation needed.

#### Launch the GUI

```bash
uv run streamlit run src/supersonic_atomizer/gui/streamlit_app.py
```

Or use the helper script:

```bash
# Windows
run20_gui.bat

# POSIX
./run20_gui.sh
```

The GUI opens in your default browser at **http://127.0.0.1:8501**. Use it to
create cases, set simulation conditions, run the solver, and view results —
without editing YAML directly.

#### FastAPI GUI (port 8502)

An alternative browser-based GUI implemented with FastAPI + vanilla JavaScript:

```bash
uv run uvicorn supersonic_atomizer.gui.fastapi_app:app --host 127.0.0.1 --port 8502 --reload
```

Or use the helper script:

```bash
# Windows
run21_fastapi_gui.bat

# POSIX
./run21_fastapi_gui.sh
```

Opens at **http://127.0.0.1:8502**. Provides the same six-tab interface
(Conditions, Grid, Solve, Graphs, Table, Settings) as the Streamlit GUI through
a REST API backend with JSON polling — no Streamlit dependency required at runtime.

#### Run Tests

```bash
uv run pytest tests/ -v
```

### 3B. Helper Scripts

If you prefer not to type `uv` commands manually, use the launcher scripts in the project root.

#### Windows `.bat`

```bat
run10_uv_venv.bat
run11_uv_sync.bat
run12_app_start.bat
run13_uv_run.bat supersonic-atomizer examples\air_nozzle.yaml
run14_uv_test.bat
run15_uv_add_dev.bat ruff
run16_uv_add_prd.bat numpy
run17_uv_sync.bat
run20_gui.bat              :: Streamlit GUI  (port 8501)
run21_fastapi_gui.bat      :: FastAPI GUI    (port 8502)
```

#### POSIX `.sh`

```bash
./run10_uv_venv.sh
./run11_uv_sync.sh
./run12_app_start.sh
./run13_uv_run.sh supersonic-atomizer examples/air_nozzle.yaml
./run14_uv_test.sh
./run15_uv_add_dev.sh ruff
./run16_uv_add_prd.sh numpy
./run17_uv_sync.sh
./run20_gui.sh             # Streamlit GUI  (port 8501)
./run21_fastapi_gui.sh     # FastAPI GUI    (port 8502)
```

On Linux or macOS, make the shell scripts executable once if needed:

```bash
chmod +x run10_uv_venv.sh run11_uv_sync.sh run12_app_start.sh run13_uv_run.sh run14_uv_test.sh run15_uv_add_dev.sh run16_uv_add_prd.sh run17_uv_sync.sh run20_gui.sh run21_fastapi_gui.sh
```

### 4. Check Outputs

After a successful run, outputs appear in the directory specified by `outputs.output_directory` in the YAML file (e.g. `outputs/air_nozzle/`):

```
outputs/air_nozzle/run-<timestamp>/
  ├── results.csv          # Tabular axial results
  ├── results.json         # Structured results + metadata
  └── plots/
      ├── pressure.png
      ├── temperature.png
      ├── working_fluid_velocity.png
      ├── droplet_velocity.png
      ├── mach_number.png
      ├── droplet_mean_diameter.png
      ├── droplet_maximum_diameter.png
      └── weber_number.png
```

---

## CLI Options

```
usage: supersonic-atomizer [-h] [--startup-only] case_path

Run the Supersonic Atomizer simulation workflow.

positional arguments:
  case_path       Path to the YAML case file.

optional arguments:
  --startup-only  Run startup-stage dependency construction only
                  (validates config, builds geometry/thermo — no solver execution).
```

---

## YAML Case File Format

A case file defines one simulation. All values use **SI units**.

```yaml
fluid:
  working_fluid: air          # "air" or "steam"

boundary_conditions:
  Pt_in: 205000.0             # Inlet total pressure [Pa]
  Tt_in: 450.0                # Inlet total temperature [K]
  Ps_out: 200000.0            # Outlet static pressure [Pa]

geometry:
  x_start: 0.0                # Axial start [m]
  x_end: 0.1                  # Axial end [m]
  n_cells: 20                 # Number of grid cells
  area_distribution:
    type: table
    x: [0.0, 0.025, 0.05, 0.075, 0.1]      # Axial positions [m]
    A: [0.0001, 0.00009, 0.00008, 0.00009, 0.0001]  # Area values [m²]

droplet_injection:
  droplet_velocity_in: 5.0          # Initial droplet velocity [m/s]
  droplet_diameter_mean_in: 0.0001  # Initial mean diameter [m]
  droplet_diameter_max_in: 0.0002   # Initial max diameter [m]

models:
  breakup_model: weber_critical       # Breakup model selection
  critical_weber_number: 12.0         # We threshold for breakup
  breakup_factor_mean: 0.5            # d_mean reduction factor (0, 1)
  breakup_factor_max: 0.75            # d_max reduction factor (0, 1)
  # steam_property_model: equilibrium_mvp  # Required for steam cases

outputs:
  output_directory: outputs/my_case
  write_csv: true
  write_json: true
  generate_plots: true
```

### Supported Working Fluids

| Fluid | Description |
|---|---|
| `air` | Ideal-gas air model |
| `steam` | Equilibrium MVP steam model (IF97-ready interface) |

For steam cases, add `steam_property_model: equilibrium_mvp` under `models`.

---

## Project Structure

```
├── docs/              # Specification, architecture, and task documents
├── examples/          # Example YAML case files
│   ├── air_nozzle.yaml
│   └── steam_nozzle.yaml
├── src/
│   └── supersonic_atomizer/
│       ├── app/       # Application orchestration and result assembly
│       ├── breakup/   # Breakup model interface + Weber-critical model
│       ├── cli/       # Thin CLI entry point
│       ├── common/    # Shared error classes
│       ├── config/    # YAML loading, validation, defaults, translation
│       ├── domain/    # Case, state, and result data models
│       ├── geometry/  # Area profile and geometry model
│       ├── grid/      # Axial grid generation
│       ├── io/        # CSV and JSON writers
│       ├── plotting/  # Matplotlib profile plots
│       ├── solvers/
│       │   ├── gas/       # Quasi-1D isentropic gas solver
│       │   └── droplet/   # Droplet transport with drag
│       ├── thermo/    # Thermo provider interface (air, steam)
│       └── validation/ # Post-solve sanity checks and reporting
├── tests/             # Unit, integration, and contract tests
├── outputs/           # Generated simulation outputs
├── pyproject.toml     # Project metadata and dependencies (managed by uv)
├── uv.lock            # Reproducible dependency lock file
└── README.md
```

---

## Key Documents

| Document | Description |
|---|---|
| [docs/spec.md](docs/spec.md) | Product specification and requirements |
| [docs/architecture.md](docs/architecture.md) | System architecture and module boundaries |
| [docs/tasks.md](docs/tasks.md) | Task plan across all implementation phases |

---

## Physics Summary

- **Gas:** Steady quasi-1D compressible flow, isentropic with area-Mach closure
- **Droplets:** Representative droplet transport, slip-velocity-driven spherical drag
- **Breakup:** Weber number threshold — when $We > We_{crit}$, diameters are reduced by configured factors
- **Coupling:** One-way (gas → droplets); droplet feedback to gas is neglected

### Limitations (MVP)

- No 3D CFD, no turbulence modeling
- No droplet-droplet collision/coalescence
- No wall-film physics, no evaporation
- No frictional losses
- Subsonic foundation path only (no choking/supersonic branch handling)
- Steam uses equilibrium-vapor approximation (full IF97 deferred)

---

## License

See repository license file for details.
