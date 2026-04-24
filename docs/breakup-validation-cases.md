# Breakup Validation Cases

Minimal validation cases for breakup behavior:

- **No-Breakup Case**: a low-slip, low-Weber case where breakup should not trigger.
- **Triggered Breakup Case**: a high-slip case where `We > We_{crit}` and diameter reduction occurs.

- **Triggered Breakup Case**: a high-slip case where `We > We_{crit}` and diameter reduction occurs (i.e., exceeds the critical threshold).

- Include explicit notes for cases where conditions are below the critical threshold (i.e., below the critical threshold) and should not trigger breakup.

Include example YAML and expected outcomes for both cases.

 - For the **No-Breakup Case**, assert that diameter metrics remain unchanged over the domain (diameter metrics remain unchanged) in expected outputs.

 - For the **Triggered Breakup Case**, assert that mean and maximum diameters decrease after breakup (mean and maximum diameters decrease) in expected outputs.

 - For naming consistency, include a **Breakup-Trigger Case** entry in validation suites for CI.