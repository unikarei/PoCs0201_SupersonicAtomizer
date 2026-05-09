# Supersonic Atomizer GUI — API Endpoints

## Overview

The FastAPI GUI provides REST endpoints organized across six routers:

- **Cases** — project and case CRUD operations
- **Simulation** — background job management for solver runs
- **Chat** — case-aware chat threads and config-change proposals
- **Units** — unit preference management
- **Index** — main HTML shell
- **Debug** — client-side logging

**Base URL**: `http://localhost:8000`

**Design Pattern**: Non-blocking. Solver runs execute in background threads; clients poll `/status/{job_id}` until completion, then fetch `/result/{job_id}`.

---

## 1. Index Router

Serves the single-page application shell.

### GET `/`

Serve the main HTML page.

**Response**: HTML document (index.html) via Jinja2 template.

**Side Effect**: Sets session cookie if not present.

---

### GET `/favicon.ico`

Favicon handler to suppress 404 noise.

**Response**: 204 No Content.

---

## 2. Cases Router

Project and case CRUD. Supports both flat (legacy) and project-scoped case storage.

**Prefix**: `/api/cases`

### Projects

#### GET `/projects/`

List all project names and the default project.

**Response**:
```json
{
  "projects": ["default", "project1", ...],
  "default_project": "default"
}
```

**Status Codes**: `200 OK`

---

#### POST `/projects/`

Create a new (empty) project.

**Request Body**:
```json
{
  "name": "my_project"
}
```

**Response**:
```json
{
  "name": "my_project"
}
```

**Status Codes**: `201 Created` | `400 Bad Request` (invalid name) | `409 Conflict` (project exists)

---

#### DELETE `/projects/{project}`

Delete a project and all cases within it.

**Path Parameters**:
- `project` (str) — project name

**Status Codes**: `204 No Content` | `400 Bad Request` | `404 Not Found`

---

#### POST `/projects/{project}/rename`

Rename a project; preserves contained cases.

**Path Parameters**:
- `project` (str) — current project name

**Request Body**:
```json
{
  "new_name": "renamed_project"
}
```

**Response**:
```json
{
  "name": "renamed_project"
}
```

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found` | `409 Conflict` (name taken)

---

#### GET `/projects/{project}/export`

Export all YAML cases in a project as a ZIP archive.

**Path Parameters**:
- `project` (str) — project name

**Response**: Binary ZIP file attachment.

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found`

---

### Cases (Project-Scoped)

#### GET `/projects/{project}/cases/`

List all case names in a project.

**Path Parameters**:
- `project` (str) — project name

**Response**:
```json
{
  "project": "my_project",
  "cases": ["case1", "case2", ...]
}
```

**Status Codes**: `200 OK` | `400 Bad Request`

---

#### POST `/projects/{project}/cases/`

Create a new empty skeleton case in the project.

**Path Parameters**:
- `project` (str) — project name

**Request Body**:
```json
{
  "name": "new_case"
}
```

**Response**:
```json
{
  "project": "my_project",
  "name": "new_case"
}
```

**Status Codes**: `201 Created` | `400 Bad Request` | `409 Conflict` (exists)

---

#### GET `/projects/{project}/cases/{name}`

Load and return a case config dict with metadata.

**Path Parameters**:
- `project` (str) — project name
- `name` (str) — case name

**Response**:
```json
{
  "config": { ...full case config dict... },
  "has_result": true|false,
  "last_modified": "2026-05-09T10:30:00Z"
}
```

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found`

---

#### PUT `/projects/{project}/cases/{name}`

Save/overwrite a case config dict.

**Path Parameters**:
- `project` (str) — project name
- `name` (str) — case name

**Request Body**: Full case config dict (same structure as GET response).

**Response**: Same as GET.

**Status Codes**: `200 OK` | `400 Bad Request` (validation failed) | `404 Not Found`

---

#### DELETE `/projects/{project}/cases/{name}`

Delete a case and its associated output artifacts.

**Path Parameters**:
- `project` (str) — project name
- `name` (str) — case name

**Status Codes**: `204 No Content` | `400 Bad Request` | `404 Not Found`

---

#### POST `/projects/{project}/cases/{name}/duplicate`

Create a copy of an existing case.

**Path Parameters**:
- `project` (str) — project name
- `name` (str) — source case name

**Request Body**:
```json
{
  "new_name": "case_copy"
}
```

**Response**:
```json
{
  "project": "my_project",
  "name": "case_copy"
}
```

**Status Codes**: `201 Created` | `400 Bad Request` | `404 Not Found` | `409 Conflict`

---

#### POST `/projects/{project}/cases/{name}/rename`

Rename a case and preserve output artifacts.

**Path Parameters**:
- `project` (str) — project name
- `name` (str) — current case name

**Request Body**:
```json
{
  "new_name": "renamed_case"
}
```

**Response**:
```json
{
  "project": "my_project",
  "name": "renamed_case"
}
```

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found` | `409 Conflict`

---

#### GET `/projects/{project}/cases/{name}/export`

Export a single case as a ZIP archive containing its YAML and output artifacts.

**Path Parameters**:
- `project` (str) — project name
- `name` (str) — case name

**Response**: Binary ZIP file attachment.

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found`

---

#### GET `/projects/{project}/cases/{name}/last_result`

Retrieve the most recent simulation result for a case without re-running.

**Path Parameters**:
- `project` (str) — project name
- `name` (str) — case name

**Response**: Same structure as `/api/simulation/result/{job_id}` (plots, table rows, CSV).

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found` | `409 Conflict` (no result)

---

### Cases (Legacy Flat Storage)

For backward compatibility, endpoints without a project path operate on root-level cases (legacy flat mode) or default project cases.

#### GET `/`

List all root-level case names (legacy flat mode).

**Response**:
```json
{
  "cases": ["case1", "case2", ...]
}
```

**Status Codes**: `200 OK`

---

#### POST `/`

Create a new empty skeleton case at root level (legacy mode).

**Request Body**:
```json
{
  "name": "new_case"
}
```

**Response**:
```json
{
  "name": "new_case"
}
```

**Status Codes**: `201 Created` | `400 Bad Request` | `409 Conflict`

---

#### GET `/{name}`

Load and return a root-level case config (legacy mode).

**Path Parameters**:
- `name` (str) — case name

**Response**: Case config dict with metadata.

**Status Codes**: `200 OK` | `404 Not Found`

---

#### PUT `/{name}`

Save/overwrite a root-level case (legacy mode).

**Path Parameters**:
- `name` (str) — case name

**Request Body**: Full case config dict.

**Response**: Case config dict with metadata.

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found`

---

#### DELETE `/{name}`

Delete a root-level case (legacy mode).

**Path Parameters**:
- `name` (str) — case name

**Status Codes**: `204 No Content` | `404 Not Found`

---

#### GET `/{name}/last_result`

Retrieve the most recent result for a root-level case (legacy mode).

**Path Parameters**:
- `name` (str) — case name

**Response**: Plots, table rows, CSV.

**Status Codes**: `200 OK` | `404 Not Found` | `409 Conflict`

---

## 3. Simulation Router

Background job management for solver runs.

**Prefix**: `/api/simulation`

**Design**: Non-blocking. POST starts a background thread; GET polls status; GET retrieves result once complete.

### POST `/run`

Start a simulation run in the background.

**Request Body**:
```json
{
  "project_name": "my_project" | null,
  "case_name": "my_case",
  "config": { ...optional multi-value config for sweep... } | null
}
```

- `config` (optional): Multi-value parameter dict to expand into a batch. If omitted, runs single case.

**Response**:
```json
{
  "job_id": "uuid-string"
}
```

**Status Codes**: `200 OK` | `400 Bad Request` (validation failed) | `404 Not Found` (case not found)

**Side Effect**: Spawns daemon thread to run solver; stores job in job store.

---

### GET `/status/{job_id}`

Poll the status of a background simulation job.

**Path Parameters**:
- `job_id` (str) — UUID returned by POST /run

**Response**:
```json
{
  "status": "running" | "completed" | "failed",
  "error": null | "error message string"
}
```

**Status Codes**: `200 OK` | `404 Not Found` (job not found)

---

### GET `/result/{job_id}`

Retrieve plots, table rows, and CSV for a completed job.

Must be called only after status returns `"completed"`.

**Path Parameters**:
- `job_id` (str) — UUID

**Response**:
```json
{
  "plots": {
    "plot_name_1": "base64-encoded-png-string",
    "plot_name_2": "base64-encoded-png-string",
    ...
  },
  "table_rows": [
    { "column1": value, "column2": value, ... },
    ...
  ],
  "csv_content": "comma,separated,values\n...",
  "run_count": 1 | 2+ (if multi-value batch)
}
```

**Status Codes**: `200 OK` | `404 Not Found` | `409 Conflict` (job not completed)

---

## 4. Chat Router

Case-aware chat threads and AI-assisted config-change workflows.

**Prefix**: `/api/chat`

### Chat Threads

#### GET `/threads?case_name=...&project_name=...` (optional)

List persisted chat threads for a case.

**Query Parameters**:
- `case_name` (str, required) — case name
- `project_name` (str | null, optional) — project name

**Response**:
```json
{
  "threads": [
    {
      "id": "uuid",
      "title": "Thread title",
      "created_at": "2026-05-09T10:00:00Z",
      "updated_at": "2026-05-09T10:30:00Z"
    },
    ...
  ]
}
```

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found` (case not found)

---

#### POST `/threads`

Create a new chat thread for a case.

**Request Body**:
```json
{
  "project_name": "my_project" | null,
  "case_name": "my_case",
  "title": "Initial thread title"
}
```

**Response**:
```json
{
  "id": "uuid",
  "title": "Initial thread title",
  "created_at": "2026-05-09T10:00:00Z",
  "updated_at": "2026-05-09T10:00:00Z",
  "messages": []
}
```

**Status Codes**: `201 Created` | `400 Bad Request` | `404 Not Found`

---

#### GET `/threads/{thread_id}?case_name=...&project_name=...` (optional)

Load a persisted chat thread with full message history.

**Path Parameters**:
- `thread_id` (str) — thread UUID

**Query Parameters**:
- `case_name` (str, required)
- `project_name` (str | null, optional)

**Response**:
```json
{
  "id": "uuid",
  "title": "...",
  "created_at": "2026-05-09T10:00:00Z",
  "updated_at": "2026-05-09T10:30:00Z",
  "messages": [
    { "role": "user" | "assistant" | "system", "content": "..." },
    ...
  ]
}
```

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found`

---

#### PATCH `/threads/{thread_id}`

Rename a persisted chat thread.

**Path Parameters**:
- `thread_id` (str) — thread UUID

**Request Body**:
```json
{
  "project_name": "my_project" | null,
  "case_name": "my_case",
  "title": "New thread title"
}
```

**Response**: Full thread detail (as GET).

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found`

---

#### DELETE `/threads/{thread_id}?case_name=...&project_name=...` (optional)

Delete a chat thread.

**Path Parameters**:
- `thread_id` (str) — thread UUID

**Query Parameters**:
- `case_name` (str, required)
- `project_name` (str | null, optional)

**Status Codes**: `204 No Content` | `400 Bad Request` | `404 Not Found`

---

#### PUT `/threads/{thread_id}/messages`

Replace all messages in a thread (used to load persisted history or reset).

**Path Parameters**:
- `thread_id` (str) — thread UUID

**Request Body**:
```json
{
  "project_name": "my_project" | null,
  "case_name": "my_case",
  "messages": [
    { "role": "user" | "assistant", "content": "..." },
    ...
  ]
}
```

**Response**: Full thread detail with updated messages.

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found`

---

### Chat Messages

#### POST `/messages`

Send a user message and receive an AI-generated reply.

**Request Body**:
```json
{
  "project_name": "my_project" | null,
  "case_name": "my_case",
  "thread_id": "uuid",
  "user_message": "What should I adjust?"
}
```

**Response**:
```json
{
  "role": "assistant",
  "content": "AI reply text..."
}
```

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found` | `500 Server Error` (LLM error)

---

#### POST `/summary`

Generate a concise summary of a chat thread.

**Request Body**:
```json
{
  "project_name": "my_project" | null,
  "case_name": "my_case",
  "thread_id": "uuid"
}
```

**Response**:
```json
{
  "summary": "Concise summary of the thread..."
}
```

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found` | `500 Server Error`

---

### Chat Config-Change Workflows

Implements the approval-gated transactional pattern (architecture.md §9.1).

#### POST `/config-changes/proposals`

Generate an AI-proposed config-change patch.

**Request Body**:
```json
{
  "project_name": "my_project" | null,
  "case_name": "my_case",
  "thread_id": "uuid" | null,
  "user_request": "What should I change to improve performance?",
  "scoped_paths": ["boundary_conditions", "geometry"] | null
}
```

**Response**:
```json
{
  "proposal_id": "uuid",
  "state": "proposed",
  "changes": [
    { "path": "boundary_conditions.Pt_in", "value": 250000 },
    ...
  ]
}
```

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found` | `500 Server Error`

---

#### POST `/config-changes/proposals/{proposal_id}/apply`

Apply a proposed patch and validate; returns a before/after diff.

**Path Parameters**:
- `proposal_id` (str) — proposal UUID

**Request Body**:
```json
{
  "project_name": "my_project" | null,
  "case_name": "my_case"
}
```

**Response**:
```json
{
  "proposal_id": "uuid",
  "state": "applied",
  "before_after_diffs": [
    { "path": "boundary_conditions.Pt_in", "before": 200000, "after": 250000 },
    ...
  ]
}
```

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found` | `422 Unprocessable Entity` (validation failed)

---

#### POST `/config-changes/proposals/{proposal_id}/confirm`

Confirm the applied patch and persist to case YAML.

**Path Parameters**:
- `proposal_id` (str) — proposal UUID

**Request Body**:
```json
{
  "project_name": "my_project" | null,
  "case_name": "my_case"
}
```

**Response**:
```json
{
  "proposal_id": "uuid",
  "state": "confirmed",
  "updated_case": { ...full case config after changes... }
}
```

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found` | `409 Conflict` (state not `applied`)

---

#### POST `/config-changes/proposals/{proposal_id}/reject`

Reject a proposed patch and discard it.

**Path Parameters**:
- `proposal_id` (str) — proposal UUID

**Request Body**:
```json
{
  "project_name": "my_project" | null,
  "case_name": "my_case"
}
```

**Response**:
```json
{
  "proposal_id": "uuid",
  "state": "rejected"
}
```

**Status Codes**: `200 OK` | `400 Bad Request` | `404 Not Found` | `409 Conflict`

---

## 5. Units Router

Unit preference management for display conversions.

**Prefix**: `/api/units`

### GET `/preferences`

Return the current per-group unit preferences.

**Response**:
```json
{
  "pressure": "Pa",
  "temperature": "K",
  "length": "m",
  "velocity": "m/s",
  ...
}
```

**Status Codes**: `200 OK`

---

### PATCH `/preferences`

Apply partial updates to unit preferences.

**Request Body**:
```json
{
  "pressure": "bar",
  "temperature": "°C"
}
```

**Response**: Updated full preferences dict (as GET).

**Status Codes**: `200 OK` | `400 Bad Request` (invalid unit)

---

### GET `/groups`

Return all unit groups with conversion specs.

**Response**:
```json
{
  "pressure": {
    "Pa": { "scale": 1.0, "offset": 0.0 },
    "bar": { "scale": 1e-5, "offset": 0.0 },
    "atm": { "scale": 9.8692e-6, "offset": 0.0 }
  },
  "temperature": {
    "K": { "scale": 1.0, "offset": 0.0 },
    "°C": { "scale": 1.0, "offset": -273.15 }
  },
  ...
}
```

Where: `display_value = si_value * scale + offset`

**Status Codes**: `200 OK`

---

## 6. Debug Router

Client-side logging utilities.

**Prefix**: `/api/debug`

### POST `/log`

Accept small client-side debug messages for server-side investigation.

**Request Body**:
```json
{
  "message": "Error message from client",
  "details": "Additional context (optional)"
}
```

**Response**: `null`

**Status Codes**: `200 OK`

---

## Error Response Format

All error responses follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

**HTTP Status Codes**:

| Code | Meaning |
|------|---------|
| 200  | Success |
| 201  | Created |
| 204  | No Content (success, no response body) |
| 400  | Bad Request (validation, naming, format) |
| 404  | Not Found (case, job, thread, etc.) |
| 409  | Conflict (resource exists, state mismatch) |
| 422  | Unprocessable Entity (validation failed) |
| 500  | Internal Server Error |

---

## Typical Workflows

### Single Simulation Run

1. `POST /api/simulation/run` with `case_name` → get `job_id`
2. Poll `GET /api/simulation/status/{job_id}` until status = `"completed"`
3. `GET /api/simulation/result/{job_id}` → plots, table, CSV

### Multi-Value Sweep

1. `POST /api/simulation/run` with `case_name` and `config` (multi-value dict) → get `job_id`
2. Poll `GET /api/simulation/status/{job_id}`
3. `GET /api/simulation/result/{job_id}` → overlay plots + aggregated table

### AI-Assisted Config Change

1. `POST /api/chat/config-changes/proposals` → get `proposal_id`
2. `POST /api/chat/config-changes/proposals/{proposal_id}/apply` → review diff
3. `POST /api/chat/config-changes/proposals/{proposal_id}/confirm` → persist
4. Run simulation with updated case

---

## References

- Architecture: [docs/architecture.md](architecture.md)
- Application Service: `src/supersonic_atomizer/app/services.py`
- GUI Routers: `src/supersonic_atomizer/gui/routers/`
