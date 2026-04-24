# Droplet Injection Assumptions

This document describes the assumptions for droplet injection in the MVP.

Required items:

- injection location
- initial droplet velocity
- initial mean droplet diameter and initial maximum droplet diameter

Optional parameters include injected `water_mass_flow_rate` or equivalent loading metrics.

By convention the injection location is the **inlet-side start of the axial domain** (i.e. `x_start`) unless an alternative injection location is specified in the case.
- Validation rule: the maximum diameter should not be smaller than the mean diameter; enforce `d_max >= d_mean` in semantic validation.