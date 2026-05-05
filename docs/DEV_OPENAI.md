# Local OpenAI / LLM setup (development)

This document describes recommended ways to persist and validate an OpenAI-compatible API key for local development.

1) Use a local `.env` file (recommended for development)

- Copy `.env.example` to `.env` at the project root and fill in your key:

```
OPENAI_API_KEY=sk-xxxx-your-key-xxxx
OPENAI_MODEL=gpt-4.1-mini
OPENAI_BASE_URL=https://api.openai.com/v1
```

- Do NOT commit `.env` to source control. Ensure `.gitignore` excludes it.
- The application loads `.env` automatically on startup (non-destructively).

2) Persist into your user environment (Windows)

- To set the key for the current user (so new shells see it):

```powershell
setx OPENAI_API_KEY "sk-...your-key..."
```

- For the current PowerShell session only (temporary):

```powershell
$env:OPENAI_API_KEY = 'sk-...your-key...'
```

3) Startup validation (implemented)

- The FastAPI app performs a light validation of `OPENAI_API_KEY` on startup by requesting the models endpoint and logs a warning if the key appears invalid (HTTP 401) or if validation fails due to network issues.
- Control this behaviour with `OPENAI_VALIDATE_ON_START` (set to `0` to disable).

4) Troubleshooting

- If the server logs a 401 on startup or chat requests return 502/503, verify the key in your `.env` or user environment and check the OpenAI dashboard for the key status.
- If your environment blocks outbound HTTP requests, startup validation may fail — set `OPENAI_VALIDATE_ON_START=0` to avoid the network check.

5) CI / Production

- Do not store secrets in repo files or plain `.env` in CI. Use your CI provider's secret management and set the necessary environment variables for the test/production runs.
