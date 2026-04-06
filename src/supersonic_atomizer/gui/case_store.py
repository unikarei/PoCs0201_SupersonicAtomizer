"""Case persistence — backed by YAML files in the ``cases/`` directory.

Each case file is structurally identical to the input format consumed by
``config/loader.py``, so any saved case can be loaded directly by the CLI
or application service without conversion.

Architectural boundary (architecture.md, Appendix B.3 + B.5):
- ``CaseStore`` owns ALL case-persistence logic.
- No other gui/ module reads or writes case files directly.
- The GUI never constructs YAML manually; it passes raw config dicts here
  and ``CaseStore`` serialises them.
- Cases are identified by a short name (safe filename characters only).
  The physical file is ``<cases_dir>/<name>.yaml``.

Error handling
--------------
- ``CaseNotFoundError`` — named case does not exist in the store.
- ``CaseNameError``     — the name contains characters that are not safe
                          for use as a filename component.
- ``CasePersistenceError`` — IO or YAML serialisation failure.

These are plain ``ValueError``/``OSError`` subclasses so callers can catch
them without importing the full ``supersonic_atomizer.common`` error taxonomy
(which belongs to solver layers, not the GUI layer).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

# ── Sentinel for default cases_dir ───────────────────────────────────────────
_DEFAULT_CASES_DIR = Path("cases")

# Safe name pattern: letters, digits, underscores, hyphens (no spaces / path
# separators).  Mirrors the convention used for run-output directory names.
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_\-]{1,128}$")

# Default template written when ``create()`` is called — a minimal valid YAML
# case that passes schema and semantic validation.
_DEFAULT_TEMPLATE: dict[str, Any] = {
    "fluid": {"working_fluid": "air"},
    "boundary_conditions": {
        "Pt_in": 200_000.0,
        "Tt_in": 400.0,
        "Ps_out": 101_325.0,
    },
    "geometry": {
        "x_start": 0.0,
        "x_end": 0.1,
        "n_cells": 100,
        "area_distribution": {
            "type": "table",
            "x": [0.0, 0.05, 0.1],
            "A": [1.0e-4, 6.0e-5, 5.0e-5],
        },
    },
    "droplet_injection": {
        "droplet_velocity_in": 10.0,
        "droplet_diameter_mean_in": 50e-6,
        "droplet_diameter_max_in": 100e-6,
    },
    "models": {
        "breakup_model": "weber_critical",
        "critical_weber_number": 12.0,
        "breakup_factor_mean": 0.5,
        "breakup_factor_max": 0.5,
    },
    "outputs": {
        "output_directory": "outputs",
        "write_csv": True,
        "write_json": True,
        "generate_plots": True,
    },
}


# ── Exceptions ────────────────────────────────────────────────────────────────


class CaseNotFoundError(KeyError):
    """Raised when a requested case name does not exist in the store."""


class CaseNameError(ValueError):
    """Raised when a case name contains characters that are unsafe as a filename."""


class CasePersistenceError(OSError):
    """Raised when a case file cannot be read from or written to disk."""


# ── CaseStore ─────────────────────────────────────────────────────────────────


class CaseStore:
    """Persistent case management backed by YAML files.

    Parameters
    ----------
    cases_dir:
        Root directory where case YAML files are stored.  Defaults to
        ``cases/`` relative to the current working directory.  The directory
        is created on first use if it does not exist.

    Examples
    --------
    >>> store = CaseStore()
    >>> store.create("my_case")
    >>> store.list_cases()
    ['my_case']
    >>> cfg = store.load("my_case")
    >>> cfg["fluid"]["working_fluid"]
    'air'
    >>> cfg["fluid"]["working_fluid"] = "steam"
    >>> store.save("my_case", cfg)
    >>> store.load("my_case")["fluid"]["working_fluid"]
    'steam'
    """

    def __init__(self, cases_dir: str | Path | None = None) -> None:
        self._cases_dir = Path(cases_dir) if cases_dir is not None else _DEFAULT_CASES_DIR

    @property
    def cases_dir(self) -> Path:
        """Return the root directory for case YAML files (read-only)."""
        return self._cases_dir

    # ── Path helpers ──────────────────────────────────────────────────────────

    def _validate_name(self, name: str) -> None:
        """Raise ``CaseNameError`` if *name* is not a safe filename component."""
        if not _NAME_PATTERN.match(name):
            raise CaseNameError(
                f"Case name {name!r} is invalid.  "
                "Names must contain only letters, digits, underscores, or "
                "hyphens and must be between 1 and 128 characters long."
            )

    def _case_path(self, name: str) -> Path:
        """Return the absolute path for the YAML file of the named case."""
        return self._cases_dir / f"{name}.yaml"

    def _ensure_cases_dir(self) -> None:
        """Create the cases directory if it does not already exist."""
        self._cases_dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def create(self, name: str, template: dict[str, Any] | None = None) -> Path:
        """Create a new case with the given name and write the default template.

        Parameters
        ----------
        name:
            Unique case identifier.  Must match ``[A-Za-z0-9_\\-]{1,128}``.
        template:
            Optional seed configuration dict.  When ``None`` the built-in
            default template is used.

        Returns
        -------
        Path
            The path to the newly created YAML file.

        Raises
        ------
        CaseNameError
            If *name* contains unsafe characters.
        CasePersistenceError
            If the file cannot be written to disk.
        FileExistsError
            If a case with this name already exists.
        """
        self._validate_name(name)
        self._ensure_cases_dir()

        path = self._case_path(name)
        if path.exists():
            raise FileExistsError(f"Case {name!r} already exists at {path}.")

        config = template if template is not None else _DEFAULT_TEMPLATE
        self._write_yaml(path, config)
        return path

    def list_cases(self) -> list[str]:
        """Return a sorted list of case names stored in the cases directory.

        Cases are discovered by finding ``*.yaml`` files in the root cases
        directory (non-recursive).  Returns an empty list when the directory
        does not exist yet.
        """
        if not self._cases_dir.is_dir():
            return []
        names = sorted(p.stem for p in self._cases_dir.glob("*.yaml"))
        return names

    def load(self, name: str) -> dict[str, Any]:
        """Load a case by name and return its raw configuration dict.

        Parameters
        ----------
        name:
            Case name to load (without the ``.yaml`` extension).

        Returns
        -------
        dict[str, Any]
            The raw YAML content of the case file as a Python dict.
            The structure is identical to what ``config/loader.py`` returns.

        Raises
        ------
        CaseNameError
            If *name* contains unsafe characters.
        CaseNotFoundError
            If the named case does not exist in the store.
        CasePersistenceError
            If the file cannot be read or parsed.
        """
        self._validate_name(name)
        path = self._case_path(name)

        if not path.exists():
            raise CaseNotFoundError(
                f"Case {name!r} not found in {self._cases_dir}."
            )

        return self._read_yaml(path)

    def save(self, name: str, config: dict[str, Any]) -> Path:
        """Persist a configuration dict as the named case YAML file.

        Creates the case file if it does not exist; overwrites it if it does.

        Parameters
        ----------
        name:
            Case name (without the ``.yaml`` extension).
        config:
            Raw configuration dict.  Must be YAML-serialisable.  The caller
            is responsible for ensuring the content is structurally compatible
            with ``config/loader.py``.

        Returns
        -------
        Path
            The path to the written YAML file.

        Raises
        ------
        CaseNameError
            If *name* contains unsafe characters.
        CasePersistenceError
            If the file cannot be written.
        """
        self._validate_name(name)
        self._ensure_cases_dir()
        path = self._case_path(name)
        self._write_yaml(path, config)
        return path

    def delete(self, name: str) -> None:
        """Remove a case from the store.

        Parameters
        ----------
        name:
            Case name to remove.

        Raises
        ------
        CaseNameError
            If *name* contains unsafe characters.
        CaseNotFoundError
            If the named case does not exist.
        CasePersistenceError
            If the file cannot be removed.
        """
        self._validate_name(name)
        path = self._case_path(name)
        if not path.exists():
            raise CaseNotFoundError(
                f"Case {name!r} not found in {self._cases_dir}."
            )
        try:
            path.unlink()
        except OSError as exc:
            raise CasePersistenceError(
                f"Failed to delete case {name!r}: {exc}"
            ) from exc

    def case_path(self, name: str) -> Path:
        """Return the filesystem path for the named case YAML file.

        This path is suitable for passing directly to ``load_raw_case_config``
        or ``ApplicationService.run_simulation``.  The case is not required to
        exist — callers can use this to check existence themselves.
        """
        self._validate_name(name)
        return self._case_path(name)

    def exists(self, name: str) -> bool:
        """Return True if a case with the given name exists in the store."""
        self._validate_name(name)
        return self._case_path(name).exists()

    # ── Internal IO helpers ───────────────────────────────────────────────────

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        """Read and parse a YAML file; raise ``CasePersistenceError`` on failure."""
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CasePersistenceError(
                f"Cannot read case file {path}: {exc}"
            ) from exc

        try:
            parsed = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise CasePersistenceError(
                f"Invalid YAML in case file {path}: {exc}"
            ) from exc

        if not isinstance(parsed, dict):
            raise CasePersistenceError(
                f"Case file {path} does not contain a top-level mapping."
            )

        return parsed

    def _write_yaml(self, path: Path, config: dict[str, Any]) -> None:
        """Serialise *config* to YAML and write to *path*."""
        try:
            text = yaml.dump(
                config,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
            path.write_text(text, encoding="utf-8")
        except (OSError, yaml.YAMLError) as exc:
            raise CasePersistenceError(
                f"Failed to write case file {path}: {exc}"
            ) from exc
