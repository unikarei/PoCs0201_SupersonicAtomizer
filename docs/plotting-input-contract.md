# Plotting Input Contract

This document describes the input contract for plotting functions.

- Plotting functions consume **structured simulation result data** (e.g., `SimulationResult`) and extract series for `x` and named fields.
- Plotting functions accept output or plotting settings for labels, units and figure layout.
- Plotting **does not depend on raw solver internals**; plotters should use only structured result objects.

Document required fields and series extraction rules to maintain separation between solver and plotting layers.

Note: plotting code **does not parse raw YAML** or attempt to reconstruct solver inputs; it consumes structured `SimulationResult` objects only.

- Plots and plotters must not recompute physics: plotting modules `does not recompute physics` and must rely only on structured results.

- Plotting modules are intended for `figure generation only` and must not attempt to perform physics updates or reconstructions.