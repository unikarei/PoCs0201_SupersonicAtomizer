# User Run Workflow

This document describes CLI usage and the typical user run workflow.

Typical user steps:

- prepare a YAML case file
- **run the simulator from the CLI** using `supersonic-atomizer run --case <case.yaml>`
- inspect CSV/JSON outputs in the configured output directory

Include example commands and sample outputs for users.

Outputs include CSV and JSON result files as well as generated **plot artifacts** (PNG figures) placed in the run output directory.

- The CLI and GUI should report `run status` and concise run summaries during and after execution to help users locate outputs and failures.