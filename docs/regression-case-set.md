# Regression Case Set

Placeholder listing regression reference cases used for CI checks.

Required regression entries:

- constant-area gas-only case
- converging/diverging gas-only sanity case
- zero-slip or near-zero-slip droplet case

Include case identifiers and stored reference outputs for CI regression checks.

- include a **breakup-trigger case** for regression testing of breakup behavior.

- Each regression case entry should include qualitative trend descriptions to help reviewers understand expected behavior.

- Regression entries should include numerical tolerances for automated CI checks (tolerances) to define acceptable deviations from stored reference outputs.