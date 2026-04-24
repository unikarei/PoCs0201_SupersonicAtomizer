# Drag Model Abstraction

This document describes the drag model interface and the MVP default.

- Drag models must be **replaceable** and selectable via configuration.
- The MVP default is a **simple spherical drag model** using a Reynolds-number-based drag coefficient for spherical particles.

Include equations and selection keys for alternative drag correlations.


Document **alternate drag correlations** and how to select them via configuration keys.

- Drag-model outputs should be reproducible and provide deterministic output for identical inputs (i.e., deterministic output is expected for unit tests and regression checks).