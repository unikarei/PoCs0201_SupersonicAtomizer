# Grid Generation Rules

Placeholder describing grid generation rules for `n_cells`, extents, and spacing.

Required rule topics:

- `x_end` must be greater than `x_start`
- `n_cells` must be an integer
- `node_count` should therefore be `n_cells + 1`
- include both physical domain endpoints
- uniform spacing (unless explicitly configured otherwise)
- fail explicitly on invalid grid inputs

TODO: list validation and defaulting behavior.