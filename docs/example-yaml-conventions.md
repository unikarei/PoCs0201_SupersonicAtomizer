# Example YAML Conventions

This document lists example YAML conventions and fields accepted by the runtime.

Common keys include `working_fluid`, `Pt_in`, `Tt_in`, `Ps_out`, and `A(x)` area definitions.

Optional keys used by steam cases: `inlet_wetness`.

Include a minimal example YAML case demonstrating required and optional fields.

YAML-driven configuration also supports **breakup model selection** via `ModelSelectionConfig` keys such as `weber_threshold`.