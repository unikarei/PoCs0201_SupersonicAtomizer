**Output Organization — SDD**

Purpose
-------
This document specifies the storage, layout, retention, and serving behavior
for runtime output artifacts (CSV, JSON, plots, diagnostics, reports) produced
by the Supersonic Atomizer application. It prescribes a Project/Case/run-id
directory layout, a "latest-only" retention policy per case, and server
behaviour to serve pre-generated artifacts for instantaneous GUI display.

Scope
-----
- Applies to artifacts written when a simulation run completes: CSV, JSON,
  diagnostics, and plot PNGs.
- Affects runtime code in `src/supersonic_atomizer/io/paths.py`,
  `src/supersonic_atomizer/app/services.py`, and
  `src/supersonic_atomizer/gui/routers/cases_router.py`.
- GUI behaviour: Graph/Table/Report tabs should immediately display stored
  artifacts if the user selects a case while those artifacts exist on disk.

Requirements
------------
- R1 (Layout): Outputs shall be stored under `<output_root>/<project>/<case>/<run-id>/...`.
- R2 (Retention): For each `<project>/<case>`, only the latest completed
  run directory (by run-id created at completion) shall be retained. Older
  `run-*` sibling directories may be removed (best-effort cleanup).
- R3 (Atomicity/Safety): Cleanup must be best-effort and must not make a
  successful run fail. Failures in pruning shall be logged but ignored.
- R4 (Serving): When the GUI requests the last-result for a case and artifact
  files exist on disk, the server shall prefer returning those file contents
  (plot PNG base64, CSV text) rather than regenerating images on-demand.
- R5 (Fallback): If files are missing or unreadable, the server shall fall
  back to in-memory generation (Matplotlib) so the user still sees results.
- R6 (Compatibility): Legacy flat `outputs/run-id` layout must remain
  readable by the system (backwards-compatible fallback if project/case
  cannot be determined).

Directory Layout
----------------
- Example:

  outputs/
    ProjectA/
      CaseX/
        run-20260504T123456Z/
          results.csv
          results.json
          diagnostics.json
          plots/
            pressure.png
            temperature.png

- `run-<timestamp>Z` naming convention is required for predictable matching
  and pruning.

Retention and Cleanup
---------------------
- After a run finishes and artifacts are flushed to disk, the application
  should call a best-effort pruning routine that removes sibling directories
  under `<output_root>/<project>/<case>/` whose names start with `run-`,
  except the active run.
- The routine must:
  - Only remove directories with names starting with `run-`.
  - Attempt file deletions and directory removals but ignore failures.
  - Never raise an exception that would change the run status.

Server API Behaviour
-------------------
- Endpoint: `GET /api/cases/{name}/last_result` and
  `GET /api/projects/{project}/cases/{name}/last_result` shall:
  - Query the job store for the latest completed run for the case.
  - If the run result contains `output_metadata` with `plot_paths` or
    `csv_path`, prefer to read those files from disk and return their
    contents (plots as base64 PNGs, CSV as raw text) in the payload.
  - If files are absent, fall back to the previous behaviour of
    regenerating base64-encoded Matplotlib figures and CSV from memory.

Traceability & Metadata
-----------------------
- `OutputMetadata` shall contain absolute (or workspace-relative) paths for
  CSV/JSON/diagnostics and the `plot_paths` dict mapping field keys to PNG
  file paths. Writers must populate these paths as part of the run result.

Acceptance Criteria
-------------------
- AC1: Given a completed run that wrote artifacts to
  `<output_root>/Project/Case/run-id/plots/*.png` and `results.csv`,
  a call to `/last_result` returns the PNGs (base64) and CSV text without
  regenerating figures.
- AC2: After a successful run, only a single `run-*` directory remains
  under the case directory (best-effort; collector can tolerate failures).
- AC3: Tests cover both file-backed serving and fallback to in-memory
  generation when files are missing.

Compatibility & Migration
------------------------
- Existing runs stored as `outputs/run-id` remain accessible: when project or
  case cannot be inferred from the case path, the system falls back to the
  legacy layout.
- Migration steps (manual): move existing `outputs/run-*` into
  `outputs/default/<case>/run-*` as appropriate. A helper script may be
  provided in a later task.

Security & Permissions
----------------------
- The server reads artifact files from disk. Ensure file read permissions are
  limited to the application runtime user. Do not expose arbitrary filesystem
  paths through the API.

Testing & Validation
--------------------
- Unit tests:
  - `test_runtime_output_paths.py` should assert `build_output_metadata`
    constructs the expected `output_directory` for project/case inputs.
  - Tests for `prune_old_output_runs` should create a temporary directory
    structure and verify only the active `run-*` remains.
- Integration tests:
  - Simulate a completed run that writes artifacts and assert
    `/projects/{project}/cases/{case}/last_result` returns base64 PNGs and
    CSV text read from those files (not regenerated).

Tasks (Implementation Decomposition)
-----------------------------------
1. Update `build_output_metadata()` to accept `project` and `case_name`
   and produce `<output_root>/<project>/<case>/<run-id>` layout. (Done)
2. Ensure `ensure_output_directories()` creates per-run `plots/` directory.
   (Done)
3. Add `prune_old_output_runs()` to remove sibling `run-*` directories
   (best-effort) and call it after successful output generation. (Done)
4. Modify `/last_result` endpoints to prefer reading `plot_paths` and
   `csv_path` from `output_metadata` and return file contents if present.
   (Done)
5. Add tests validating directory layout, pruning, and file-backed serving.
6. Provide migration notes and an optional helper script to move legacy
   run folders into project/case layout.
7. Update client `selectCase()` so that when Graph tab is active it
   requests the file-backed `/last_result` and renders immediately.
8. Add logging and optional feature-flag to toggle file-backed serving.
9. Document the new layout and behaviour in user-facing docs and release notes.

Deliverables
------------
- `docs/output-organization.md` (this file)
- Unit and integration tests in `tests/` as described above.
- Optional migration script in `scripts/`.

Changelog
---------
- 2026-05-04: Initial SDD and task decomposition created by development agent.
