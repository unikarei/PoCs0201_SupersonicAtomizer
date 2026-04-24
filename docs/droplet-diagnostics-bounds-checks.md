# Droplet Diagnostics and Bounds Checks

This document lists diagnostic checks and bounds for droplet solver states.

- Detect **negative droplet velocity** values and flag as diagnostic warnings or failures.
- Detect **nonpositive mean droplet diameter** and nonpositive maximum diameter values and raise validation diagnostics.

- Detect **nonpositive maximum droplet diameter** explicitly and report as a diagnostic.

Other checks include **NaN or infinite** detection and unreasonable slip velocities.
 
- Report invalid Weber number values as a diagnostic condition (invalid Weber number) when inputs to We are out of expected ranges.

- Diagnostic reports should include a `last valid droplet state summary` when a droplet update fails or produces NaN values (last valid droplet state summary).