# Area Profile Abstraction

This document describes the `AreaProfile` abstraction used by the geometry layer.

- **`AreaProfile`**: provides `area_at(x)` queries for solver and plotting consumers.
- Key fields: `x_min`, `x_max` defining supported range, and `supports(x)` to test queries.
- Supports tabulated `(x, A)` input from raw YAML as well as analytic functions.
- The abstraction ensures consistent area interpolation semantics for the gas solver.