# Assumptions and Limitations Summary

This summary lists the core assumptions and limitations of the MVP.

- The solver models **steady quasi-1D internal flow** only.
- The droplet model uses one-way coupling (gas → droplets) and therefore assumes **one-way coupling** for MVP behavior.
- Excluded physics: 3D CFD, droplet-droplet collision, wall-film physics, detailed external jet behavior.

Documented limitations are aligned with the `spec.md` and `architecture.md` guidance.

- The MVP breakup model is a **simple Weber-threshold breakup** rule; detailed breakup physics are out of scope for MVP.

- Excluded physics (explicit): non-equilibrium condensation is not modelled in the MVP.