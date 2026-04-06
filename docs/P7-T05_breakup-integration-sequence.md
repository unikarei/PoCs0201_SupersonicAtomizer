# Breakup Integration Sequence in Droplet Solver

This document records the approved breakup integration sequence for Phase 7 Task `P7-T05`.

## Purpose

The purpose of this document is to clarify where breakup decisions occur during the droplet update cycle.

## Integration Role

The droplet solver should call the breakup model at a clearly defined position within the droplet marching sequence.

## Expected Update Order

At a conceptual level, the droplet update cycle should preserve the following order.

1. obtain the local gas state,
2. evaluate slip velocity,
3. evaluate drag response,
4. update droplet velocity,
5. compute or obtain `Weber_number` according to the approved contract,
6. call the breakup model,
7. apply breakup-driven diameter updates if triggered,
8. store the final local `DropletState` and breakup flag.

## Ordering Expectations

The integration sequence should satisfy all of the following:

- breakup occurs after the local transport quantities required by the breakup decision are available,
- breakup application is explicit rather than hidden inside unrelated solver steps,
- updated diameter metrics are reflected in the stored local droplet state,
- no-breakup outcomes preserve the pre-breakup diameter metrics for that step.

## Boundary Guidance

The following boundaries apply:

- the droplet solver owns the sequencing,
- the breakup model owns the decision and updated diameter outputs,
- the drag model remains separate from breakup logic,
- output and plotting layers report stored breakup outcomes only.

## Open Assumptions

The following assumptions remain open for later approved work:

- whether post-breakup state is stored immediately at the same axial node or staged for the next step,
- whether repeated breakup triggering at successive nodes is allowed under the MVP implementation,
- whether additional diagnostics are stored before and after breakup application.

## What This Task Does Not Do

This task defines breakup integration order only. It does not yet:

- define validation cases,
- define numerical tolerances,
- define diagnostic object structure,
- implement droplet-breakup integration code.

Those details belong to later approved tasks.
