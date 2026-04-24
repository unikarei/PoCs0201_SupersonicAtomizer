# Gas Solver Formulation Boundaries

This document describes the formulation boundaries for the MVP gas solver.

- The MVP gas solver models **steady quasi-1D internal compressible flow** and explicitly excludes high-fidelity turbulence and full multiphase CFD.
- The solver assumes a prescribed one-dimensional geometry provided via the geometry layer.
- The MVP uses **one-way coupling** (gas affects droplets; droplet feedback to gas is neglected).

Refer to `spec.md` and `architecture.md` for aligned scope and assumptions.

Explicitly excluded items include **2D or 3D CFD** simulations which are out of scope for the MVP.

- Explicitly excluded physics also include non-equilibrium condensation which is outside the MVP assumptions.