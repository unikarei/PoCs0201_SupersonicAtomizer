# Contract Test Plan

This plan lists contract tests to ensure swappable providers meet interface expectations.

- **Thermo Providers**: contract tests for air and steam provider APIs and expected property outputs.
- **Breakup Models**: contract tests for the breakup model interface and `BreakupDecision` outputs.

Enumerate providers and tests to ensure replaceability and consistent behavior.


These tests should validate **interface contracts** explicitly to ensure providers meet the expected API surface and behavior.

- Contract tests must verify that invalid-state handling is explicit and documented for each provider (e.g., invalid-state handling is explicit in failure cases).

- Contract tests should also validate that unsupported or invalid inputs fail explicitly and surface clear errors (unsupported or invalid inputs fail explicitly) rather than producing ambiguous behavior.