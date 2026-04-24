# Axial Geometry Representation

This document describes the runtime axial geometry representation used by the application.

- **`GeometryModel`**: combines axis extents and an `AreaProfile` for solver queries.
- **`x_start`** and **`x_end`**: domain start and end positions defining the axial extent.
- **`length`**: derived as `x_end - x_start` and used for diagnostics and normalization.
- **`area_profile_type`** and **`area_profile_data`**: describe whether area was provided as `tabulated` data or an analytic profile.
- The geometry model is **solver-independent** and provides consistent area queries to the gas solver.