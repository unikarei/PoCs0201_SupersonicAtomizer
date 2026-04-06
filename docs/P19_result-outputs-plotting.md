# Phase 19 — Result Assembly, Outputs, and Plotting Runtime

## Purpose

Assemble structured simulation results from gas and droplet solutions, serialize to CSV and JSON, and generate the required MVP profile plots — all through isolated output modules that consume result objects only.

## Implemented Modules

| Module | File | Responsibility |
|---|---|---|
| Result assembly | `app/result_assembly.py` | `assemble_simulation_result()`, settings-summary builder |
| Output paths | `io/paths.py` | `build_output_metadata()`, `ensure_output_directories()` |
| CSV writer | `io/csv_writer.py` | `write_simulation_result_csv()` |
| JSON writer | `io/json_writer.py` | `write_simulation_result_json()`, `simulation_result_to_dict()` |
| Profile plotter | `plotting/plot_profiles.py` | `generate_profile_plots()` |
| Plot styles | `plotting/styles.py` | `PLOT_LABELS` title/ylabel mapping |

## Result Assembly (`result_assembly.py`)

- Merges gas and droplet solutions into a `SimulationResult`.
- Validates axial-length alignment between gas and droplet outputs.
- Builds `RunDiagnostics` from merged gas/droplet diagnostics (conservative status).
- Builds a machine-readable `settings_summary` from `CaseConfig`.

## Output Path Conventions (`io/paths.py`)

- Run ID: timestamp-based `run-YYYYMMDDTHHMMSSz` by default.
- Directory structure: `{output_directory}/{run_id}/` with `plots/` subfolder.
- `build_output_metadata()` returns an `OutputMetadata` with resolved file paths.
- `ensure_output_directories()` creates directories before writing.

## CSV Writer (`io/csv_writer.py`)

14 columns in fixed order:

```
x, A, pressure, temperature, density, working_fluid_velocity, Mach_number,
droplet_velocity, slip_velocity, droplet_mean_diameter, droplet_maximum_diameter,
Weber_number, breakup_flag, droplet_reynolds_number
```

- Path resolved from explicit argument or `OutputMetadata.csv_path`.
- Raises `OutputError` on write failures.

## JSON Writer (`io/json_writer.py`)

Structure:

```json
{
  "metadata": { "case_name", "working_fluid", "output_metadata" },
  "settings_summary": { "fluid", "models", "outputs" },
  "numerical_results": { "x", "A", "pressure", ... },
  "diagnostics": { ... },
  "validation_report": { ... }
}
```

## Profile Plotter (`plotting/plot_profiles.py`)

8 required MVP plots:

| Plot | Y-label |
|---|---|
| Pressure | pressure [Pa] |
| Temperature | temperature [K] |
| Working Fluid Velocity | velocity [m/s] |
| Droplet Velocity | velocity [m/s] |
| Mach Number | Mach number [-] |
| Droplet Mean Diameter | diameter [m] |
| Droplet Maximum Diameter | diameter [m] |
| Weber Number | Weber number [-] |

- Uses `matplotlib.use("Agg")` for non-interactive rendering.
- Each plot: 6×4 inch, single line, grid enabled, tight layout, saved as PNG.
- Raises `OutputError` on file system failures.

## Key Design Decisions

- **IO modules never recompute physics** — they consume `SimulationResult` only.
- **Plotting is fully separated from solver code** — depends on result objects and style config.
- **Output path conventions are centralized** — writers resolve paths from metadata.
- **`OutputError` category** distinguishes write failures from solver failures.

## Test Files

- `tests/test_runtime_result_assembly.py`
- `tests/test_runtime_output_paths.py`
- `tests/test_runtime_csv_writer.py`
- `tests/test_runtime_json_writer.py`
- `tests/test_runtime_plot_profiles.py`

## Tasks Covered

| Task | Title |
|---|---|
| P19-T01 | Implement simulation-result assembly runtime path |
| P19-T02 | Implement output-path and artifact-metadata helpers |
| P19-T03 | Implement CSV writer runtime path |
| P19-T04 | Implement JSON writer runtime path |
| P19-T05 | Implement profile plotting runtime path |
