# Axial Grid Model

This document describes the `AxialGrid` runtime model used by the solvers.

- **`AxialGrid`**: represents node positions and spacing along the axial coordinate.
- **`x_nodes`**: ordered list of node positions along the positive axial direction.
- **`dx_values`**: local cell spacing values between nodes.
- **`node_count`** and **`cell_count`**: node and cell counts available on the object.
- The axial grid may be **uniform or non-uniform** depending on user inputs.

Validation rules include ensuring strictly increasing `x_nodes`, positive `dx_values`, and at least two nodes for marching solvers.