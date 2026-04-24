# Breakup Integration Sequence

This document describes where breakup decisions are applied during droplet updates.

- At each AxialGrid node: compute local gas state, then **evaluate slip velocity**, then compute Weber number and request breakup decision from the Breakup model.
- Breakup decisions modify droplet metrics before the next transport update.

- Per-node update order explicitly: evaluate slip velocity, evaluate drag response, then update droplet velocity, and finally apply breakup updates as required.

Pseudocode:

1. lookup gas state at `x`
2. evaluate slip velocity
3. compute Weber number
4. call the breakup model
5. apply updated diameters if breakup triggered

Additional per-node actions include **evaluate drag response** to update droplet momentum prior to breakup evaluation.

- The variable `Weber_number` (We) is computed as part of the per-node diagnostics and recorded for breakup decisions.

- The breakup model returns a breakup flag which indicates whether breakup was triggered; the solver records this `breakup flag` alongside updated diameters.