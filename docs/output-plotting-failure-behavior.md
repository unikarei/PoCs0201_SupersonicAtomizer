# Output Plotting Failure Behavior

This document describes how plotting and output failures are reported and handled.

Examples of concerns to document:

- CSV write failures
- JSON write failures
- **plot-generation failures** such as Matplotlib exceptions and image write errors
- JSON serialization issues
- classification of non-fatal vs fatal error categories for output generation.
Diagnostics should include actionable messages and recommended user steps.

Writers and plot generation failures should be **distinguishable from solver issues** in run summaries to help users identify whether a failure occurred during physics or while writing outputs.

- Output writers and plotters should include a `run summary` entry indicating whether failure occurred in solver, IO, or plotting so errors are clearly classified.

- Writers should support reporting `partial artifact success` when some outputs (e.g., CSV) succeed while others (e.g., plots) fail, so users can recover usable artifacts.