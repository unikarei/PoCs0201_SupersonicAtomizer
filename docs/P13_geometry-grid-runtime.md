# Phase 13 — Geometry and Grid Runtime Foundations

## Purpose

Build the runtime geometry and grid infrastructure so validated case inputs can produce consistent axial grids and area queries for downstream gas and droplet solvers.

## Implemented Modules

| Module | File | Responsibility |
|---|---|---|
| Axial grid | `grid/axial_grid.py` | `AxialGrid` model and `build_axial_grid()` factory |
| Area profile | `geometry/area_profile.py` | `TabulatedAreaProfile` with piecewise-linear interpolation |
| Geometry model | `geometry/geometry_model.py` | `GeometryModel` combining grid and area profile |
| Diagnostics | `geometry/diagnostics.py` | Pre-solver validation of geometry/grid alignment |

## Component Details

### `AxialGrid` (grid/axial_grid.py)

- Frozen dataclass storing `x_nodes`, `dx_values`, domain extent, and node/cell counts.
- `build_axial_grid()` generates a uniform grid from `GeometryConfig`.
- `__post_init__` validates node ordering, start/end alignment, positive spacing, and consistent counts.

### `TabulatedAreaProfile` (geometry/area_profile.py)

- Frozen dataclass storing validated `(x, A)` data as tuples.
- `area_at(x)` provides exact-match lookup and piecewise-linear interpolation.
- `build_tabulated_area_profile()` constructs from `GeometryConfig` area definition.
- Rejects nonpositive areas, non-monotonic x, and out-of-range queries.

### `GeometryModel` (geometry/geometry_model.py)

- Combines `AxialGrid` and `TabulatedAreaProfile` into a single query boundary.
- `area_at(x)` and `supports(x)` delegate to the area profile.
- `build_geometry_model()` orchestrates grid construction, profile construction, and diagnostics.
- `__post_init__` validates domain alignment between grid and profile.

### Geometry Diagnostics (geometry/diagnostics.py)

- `validate_geometry_config_diagnostics()` — malformed tabulated-domain and degenerate-grid checks before construction.
- `validate_geometry_model_diagnostics()` — grid/geometry alignment checks after assembly.

## Key Design Decisions

- The solver never sees raw area tables — it queries `GeometryModel.area_at(x)`.
- Grid construction and area interpolation are separate concerns.
- MVP supports only `"table"` area-profile type; analytic profiles can be added later.
- Interpolation method: piecewise linear between tabulated points.

## Test Files

- `tests/test_runtime_axial_grid.py`
- `tests/test_runtime_tabulated_area_profile.py`
- `tests/test_runtime_geometry_model.py`
- `tests/test_runtime_geometry_grid_diagnostics.py`

## Tasks Covered

| Task | Title |
|---|---|
| P13-T01 | Implement runtime axial-grid model and builder |
| P13-T02 | Implement runtime tabulated area-profile model |
| P13-T03 | Implement area interpolation behavior |
| P13-T04 | Implement runtime geometry assembly |
| P13-T05 | Implement geometry/grid diagnostics checks |
