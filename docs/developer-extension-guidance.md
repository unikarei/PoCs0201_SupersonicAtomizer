# Developer Extension Guidance

Guidance for adding and testing extensions such as thermo and breakup models.

Required guidance topics:

- **thermo extensions**: how to implement and register a new `ThermoProvider`.
- **breakup-model extensions**: how to register a breakup model and provide contract tests.
- contract tests for swappable providers to ensure runtime interchangeability.

- Include a reference to the `breakup-model interface` and examples showing how to implement and register a compliant breakup model.

Include checklists and example code patterns for contributors.


Also document **validation-case extensions**: how to add new validation and regression cases (YAML + expected outputs) to the `tests/data` store.

- Provide explicit references to the `thermo interface contract` and where extension authors can find it when implementing new thermo providers.

- Encourage contributors to make `small, testable changes` when adding extensions so review and CI validation remains straightforward.