# Breakup Model Interface

This document describes the breakup model API and return values (`BreakupDecision`).

- The breakup model receives the local gas-state context and local droplet state as inputs and returns a structured `BreakupDecision`.
- Inputs: local gas-state context, local droplet state, model parameters.
- Outputs: `triggered: bool`, `d_mean_new`, `d_max_new`, and diagnostic fields.

- Model parameters include the `critical Weber number` which the interface must accept or reference for Weber-threshold implementations.

Examples and contract requirements are provided for the MVP Weber-threshold model.

- The interface explicitly receives both the **local gas-state context** and the **local droplet-state context** so decisions can be made with full required inputs.

- The BreakupDecision should document the `updated mean droplet diameter` and `updated maximum droplet diameter` fields (e.g., updated mean droplet diameter => `d_mean_new`).