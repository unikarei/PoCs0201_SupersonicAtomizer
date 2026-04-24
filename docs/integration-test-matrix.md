# Integration Test Matrix

This document lists integration tests and representative end-to-end cases.

Required coverage headings:

- YAML-to-Result Execution
- Air Case Pipeline
- Steam-Provider Selection Behavior
- back-pressure sweep validation

Map each integration test to an example YAML case and expected output artifacts.

Include an **Output Generation** section describing how writers are validated in integration tests (CSV/JSON/plots).

- Integration tests and pipelines should be deterministic where practical; test harnesses should expect deterministic outputs for given inputs.

- Where automated checks are insufficient, some integration tests may require manual inspection to validate plot quality or human-judged trends (manual inspection).