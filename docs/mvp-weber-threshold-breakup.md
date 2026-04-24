# MVP Weber Threshold Breakup

This document describes the MVP Weber-threshold breakup rule and diameter update logic.

Key rule:

- Breakup trigger: We > We_{crit}

Config parameters include `critical_weber_number`, `breakup_factor_mean`, and `breakup_factor_max`.

When breakup triggers: `d_mean_new = d_mean * breakup_factor_mean` and `d_max_new = max(d_max * breakup_factor_max, d_mean_new)`.

Include formulas, units, and example parameter sets for validation cases.

The breakup rule references droplet fields such as `droplet_mean_diameter` in configuration and result schemas.

Result and config fields also include `droplet_maximum_diameter` to represent the tracked maximum diameter metric.