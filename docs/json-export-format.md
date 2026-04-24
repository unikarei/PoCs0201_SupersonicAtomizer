# JSON Export Format

This document describes the JSON output structure for results and metadata.

Required contents:

- metadata
- settings summary
- numerical results
- diagnostics

Numerical results should include arrays for `pressure`, `temperature`, `density`, `Mach number`, `working_fluid_velocity`, and droplet fields such as `droplet_mean_diameter` and `droplet_maximum_diameter`.

Include example JSON structure that contains `droplet_maximum_diameter` and other droplet metrics.

The JSON export must remain **machine-readable** and include typed arrays and metadata for downstream tools.