```markdown
# Weber Number Calculation Contract

This document defines the Weber number calculation contract used by the breakup model.

Required inputs include local gas density, slip velocity, droplet diameter, and surface tension.

- The Weber number is a **dimensionless** quantity: We = rho_g * (u_rel)^2 * d / sigma.

Document required units and example evaluations for the breakup model.

All quantities used in the Weber number evaluation shall be reported in **SI units** (kg/m^3, m/s, m, N/m) for consistency.

- Include an `Evaluation Timing` section describing when Weber number is computed relative to drag and velocity updates.

- The Weber number is the primary `breakup-driving quantity` in the MVP and must be reported in result arrays for breakup decision auditing.
```
# Weber Number Calculation Contract

This document defines the Weber number calculation contract used by the breakup model.

Required inputs include local gas density, slip velocity, droplet diameter, and surface tension.

- The Weber number is a **dimensionless** quantity: We = rho_g * (u_rel)^2 * d / sigma.

Document required units and example evaluations for the breakup model.

All quantities used in the Weber number evaluation shall be reported in **SI units** (kg/m^3, m/s, m, N/m) for consistency.

- Include an `Evaluation Timing` section describing when Weber number is computed relative to drag and velocity updates.