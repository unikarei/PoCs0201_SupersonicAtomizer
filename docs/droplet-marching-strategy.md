# Droplet Marching Strategy

This document describes how droplet states are marched along the axial grid.

- The droplet solver uses the **same axial grid used by the gas solution** and updates are synchronized to `AxialGrid` nodes.
- At each node the solver will **evaluate slip velocity**, compute drag, update droplet velocity, then compute Weber number and request breakup decisions.

Include step ordering and numerical update rules for per-node updates.

Runtime types referenced in this strategy include the `DropletState` object which holds per-node droplet velocity and diameter metrics.

- Document the expected `axial order` for per-node updates (ordering of operations along the axial coordinate).