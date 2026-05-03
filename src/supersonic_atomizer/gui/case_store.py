"""Case persistence — backed by YAML files in the ``cases/`` directory.

Each case file is structurally identical to the input format consumed by
``config/loader.py``, so any saved case can be loaded directly by the CLI
or application service without conversion.

Architectural boundary (architecture.md, Appendix B.3 + B.5):
- ``CaseStore`` owns ALL case-persistence logic.
- No other gui/ module reads or writes case files directly.
- The GUI never constructs YAML manually; it passes raw config dicts here
  and ``CaseStore`` serialises them.
- Projects and cases are identified by short safe names.
- Legacy flat cases at ``<cases_dir>/<name>.yaml`` remain readable.
- Project-scoped cases are stored at ``<cases_dir>/<project>/<name>.yaml``.

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

from dataclasses import dataclass
import io
import re
import shutil
from pathlib import Path
from typing import Any
import zipfile

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
        "coupling_mode": "one_way",
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


class ProjectNameError(ValueError):
    """Raised when a project name contains characters that are unsafe as a path component."""


class ProjectNotFoundError(KeyError):
    """Raised when a requested project does not exist in the store."""


class CasePersistenceError(OSError):
    """Raised when a case file cannot be read from or written to disk."""


@dataclass(frozen=True, slots=True)
class LegacyCaseMigrationResult:
    """Summary of moving legacy flat cases into a project directory."""

    target_project: str
    moved_cases: tuple[str, ...]
    skipped_cases: tuple[str, ...]
    dry_run: bool = False


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
    def default_project_name(self) -> str:
        """Return the default logical project name used by the GUI hierarchy."""
        return "default"

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

    def _validate_project_name(self, name: str) -> None:
        """Raise ``ProjectNameError`` if *name* is not a safe directory component."""
        if not _NAME_PATTERN.match(name):
            raise ProjectNameError(
                f"Project name {name!r} is invalid.  "
                "Names must contain only letters, digits, underscores, or "
                "hyphens and must be between 1 and 128 characters long."
            )

    def _legacy_case_path(self, name: str) -> Path:
        return self._cases_dir / f"{name}.yaml"

    def _project_dir(self, project: str) -> Path:
        return self._cases_dir / project

    def _project_case_path(self, project: str, name: str) -> Path:
        return self._project_dir(project) / f"{name}.yaml"

    def _case_path(self, name: str, project: str | None = None) -> Path:
        """Return the canonical path for the named case.

        When *project* is omitted, legacy flat storage is used for backward
        compatibility. When a project is provided, the project-scoped path is
        preferred, but the default project also falls back to a legacy flat
        case if one already exists.
        """
        if project is None:
            return self._legacy_case_path(name)

        project_path = self._project_case_path(project, name)
        if project_path.exists():
            return project_path
        if project == self.default_project_name:
            legacy_path = self._legacy_case_path(name)
            if legacy_path.exists():
                return legacy_path
        return project_path

    def _ensure_cases_dir(self) -> None:
        """Create the cases directory if it does not already exist."""
        self._cases_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_project_dir(self, project: str | None = None) -> None:
        self._ensure_cases_dir()
        if project is None:
            return
        self._project_dir(project).mkdir(parents=True, exist_ok=True)

    def _project_names_from_directories(self) -> set[str]:
        if not self._cases_dir.is_dir():
            return set()
        return {path.name for path in self._cases_dir.iterdir() if path.is_dir()}

    def _project_exists(self, project: str) -> bool:
        if project == self.default_project_name:
            return self._project_dir(project).is_dir() or any(self._cases_dir.glob("*.yaml"))
        return self._project_dir(project).is_dir()

    # ── Public API ────────────────────────────────────────────────────────────

    def create_project(self, name: str) -> Path:
        """Create a logical project directory and return its path."""
        self._validate_project_name(name)
        self._ensure_cases_dir()
        path = self._project_dir(name)
        if path.exists():
            raise FileExistsError(f"Project {name!r} already exists at {path}.")
        try:
            path.mkdir(parents=True, exist_ok=False)
        except OSError as exc:
            raise CasePersistenceError(f"Failed to create project {name!r}: {exc}") from exc
        return path

    def rename_project(self, name: str, new_name: str) -> Path:
        """Rename a project, moving all contained cases to the new project name."""
        self._validate_project_name(name)
        self._validate_project_name(new_name)
        if name == new_name:
            raise FileExistsError(f"Project {new_name!r} already exists at {self._project_dir(new_name)}.")
        if not self._project_exists(name):
            raise ProjectNotFoundError(f"Project {name!r} not found in {self._cases_dir}.")
        if self._project_exists(new_name):
            raise FileExistsError(f"Project {new_name!r} already exists at {self._project_dir(new_name)}.")

        try:
            self._ensure_cases_dir()
            target_dir = self._project_dir(new_name)

            if name == self.default_project_name:
                target_dir.mkdir(parents=True, exist_ok=False)
                for legacy_path in list(self._cases_dir.glob("*.yaml")):
                    legacy_path.replace(target_dir / legacy_path.name)
                default_dir = self._project_dir(self.default_project_name)
                if default_dir.is_dir():
                    for case_path in list(default_dir.glob("*.yaml")):
                        case_path.replace(target_dir / case_path.name)
                    if not any(default_dir.iterdir()):
                        default_dir.rmdir()
            else:
                self._project_dir(name).replace(target_dir)
        except OSError as exc:
            raise CasePersistenceError(f"Failed to rename project {name!r} to {new_name!r}: {exc}") from exc

        return target_dir

    def list_projects(self) -> list[str]:
        """Return all logical project names.

        The default project is surfaced whenever legacy flat cases exist or the
        explicit ``cases/default/`` directory exists.
        """
        names = self._project_names_from_directories()
        if self._cases_dir.is_dir() and any(self._cases_dir.glob("*.yaml")):
            names.add(self.default_project_name)
        if self._project_dir(self.default_project_name).is_dir():
            names.add(self.default_project_name)
        return sorted(names)

    def delete_project(self, name: str) -> None:
        """Delete a project and all cases contained within it."""
        self._validate_project_name(name)
        if not self._project_exists(name):
            raise ProjectNotFoundError(f"Project {name!r} not found in {self._cases_dir}.")

        try:
            if name == self.default_project_name:
                for legacy_path in self._cases_dir.glob("*.yaml"):
                    legacy_path.unlink()
            project_dir = self._project_dir(name)
            if project_dir.is_dir():
                shutil.rmtree(project_dir)
        except OSError as exc:
            raise CasePersistenceError(f"Failed to delete project {name!r}: {exc}") from exc

    def export_project_archive(self, name: str) -> bytes:
        """Return a ZIP archive containing all YAML cases in the selected project."""
        self._validate_project_name(name)
        case_names = self.list_cases(project=name)
        if not self._project_exists(name) or not case_names:
            raise ProjectNotFoundError(f"Project {name!r} not found in {self._cases_dir}.")

        buffer = io.BytesIO()
        try:
            with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
                for case_name in case_names:
                    archive.writestr(f"{name}/{case_name}.yaml", self.export_yaml(case_name, project=name))
        except OSError as exc:
            raise CasePersistenceError(f"Failed to export project {name!r}: {exc}") from exc
        return buffer.getvalue()

    def create(self, name: str, template: dict[str, Any] | None = None, *, project: str | None = None) -> Path:
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
        if project is not None:
            self._validate_project_name(project)
        self._ensure_project_dir(project)

        path = self._case_path(name, project=project)
        if path.exists():
            raise FileExistsError(f"Case {name!r} already exists at {path}.")

        config = template if template is not None else _DEFAULT_TEMPLATE
        self._write_yaml(path, config)
        return path

    def duplicate(
        self,
        source_name: str,
        target_name: str,
        *,
        project: str | None = None,
        target_project: str | None = None,
    ) -> Path:
        """Duplicate a case into a new case name, optionally across projects."""
        config = self.load(source_name, project=project)
        destination_project = target_project if target_project is not None else project
        return self.create(target_name, template=config, project=destination_project)

    def rename_case(
        self,
        source_name: str,
        target_name: str,
        *,
        project: str | None = None,
        target_project: str | None = None,
    ) -> Path:
        """Rename a case, optionally moving it to another project."""
        self._validate_name(source_name)
        self._validate_name(target_name)
        if project is not None:
            self._validate_project_name(project)
        destination_project = target_project if target_project is not None else project
        if destination_project is not None:
            self._validate_project_name(destination_project)

        source_path = self._case_path(source_name, project=project)
        if not source_path.exists():
            raise CaseNotFoundError(f"Case {source_name!r} not found in {self._cases_dir}.")

        if source_name == target_name and project == destination_project:
            raise FileExistsError(f"Case {target_name!r} already exists at {source_path}.")

        if destination_project is not None:
            self._ensure_project_dir(destination_project)
        target_path = self._case_path(target_name, project=destination_project)
        if target_path.exists():
            raise FileExistsError(f"Case {target_name!r} already exists at {target_path}.")

        try:
            source_path.replace(target_path)
            parent = source_path.parent
            if parent != self._cases_dir and parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError as exc:
            raise CasePersistenceError(
                f"Failed to rename case {source_name!r} to {target_name!r}: {exc}"
            ) from exc

        return target_path

    def list_cases(self, project: str | None = None) -> list[str]:
        """Return a sorted list of case names stored in the cases directory.

        When *project* is omitted, only legacy flat cases are returned for
        backward compatibility. When a project is provided, cases are listed
        from ``cases/<project>/``. The default project also includes legacy
        flat cases so existing user data remains visible after the hierarchy
        upgrade.
        """
        if not self._cases_dir.is_dir():
            return []
        if project is None:
            return sorted(p.stem for p in self._cases_dir.glob("*.yaml"))

        self._validate_project_name(project)
        names = set()
        project_dir = self._project_dir(project)
        if project_dir.is_dir():
            names.update(p.stem for p in project_dir.glob("*.yaml"))
        if project == self.default_project_name:
            names.update(p.stem for p in self._cases_dir.glob("*.yaml"))
        return sorted(names)

    def load(self, name: str, *, project: str | None = None) -> dict[str, Any]:
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
        if project is not None:
            self._validate_project_name(project)
        path = self._case_path(name, project=project)

        if not path.exists():
            raise CaseNotFoundError(
                f"Case {name!r} not found in {self._cases_dir}."
            )

        return self._read_yaml(path)

    def save(self, name: str, config: dict[str, Any], *, project: str | None = None) -> Path:
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
        if project is not None:
            self._validate_project_name(project)
        self._ensure_project_dir(project)
        path = self._case_path(name, project=project)
        self._write_yaml(path, config)
        return path

    def delete(self, name: str, *, project: str | None = None) -> None:
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
        if project is not None:
            self._validate_project_name(project)
        path = self._case_path(name, project=project)
        if not path.exists():
            raise CaseNotFoundError(
                f"Case {name!r} not found in {self._cases_dir}."
            )
        try:
            path.unlink()
            parent = path.parent
            if parent != self._cases_dir and parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError as exc:
            raise CasePersistenceError(
                f"Failed to delete case {name!r}: {exc}"
            ) from exc

    def export_yaml(self, name: str, *, project: str | None = None) -> str:
        """Return the raw YAML text for the selected case."""
        self._validate_name(name)
        if project is not None:
            self._validate_project_name(project)
        path = self._case_path(name, project=project)
        if not path.exists():
            raise CaseNotFoundError(
                f"Case {name!r} not found in {self._cases_dir}."
            )
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CasePersistenceError(
                f"Cannot read case file {path}: {exc}"
            ) from exc

    def migrate_legacy_cases(
        self,
        *,
        target_project: str | None = None,
        dry_run: bool = False,
    ) -> LegacyCaseMigrationResult:
        """Move legacy flat cases into the selected project directory."""
        project_name = target_project or self.default_project_name
        self._validate_project_name(project_name)
        if not self._cases_dir.is_dir():
            return LegacyCaseMigrationResult(
                target_project=project_name,
                moved_cases=(),
                skipped_cases=(),
                dry_run=dry_run,
            )

        moved_cases: list[str] = []
        skipped_cases: list[str] = []
        if not dry_run:
            self._ensure_project_dir(project_name)

        for legacy_path in sorted(self._cases_dir.glob("*.yaml")):
            destination = self._project_case_path(project_name, legacy_path.stem)
            if destination.exists():
                skipped_cases.append(legacy_path.stem)
                continue
            moved_cases.append(legacy_path.stem)
            if dry_run:
                continue
            try:
                legacy_path.replace(destination)
            except OSError as exc:
                raise CasePersistenceError(
                    f"Failed to migrate case {legacy_path.stem!r} to project {project_name!r}: {exc}"
                ) from exc

        return LegacyCaseMigrationResult(
            target_project=project_name,
            moved_cases=tuple(moved_cases),
            skipped_cases=tuple(skipped_cases),
            dry_run=dry_run,
        )

    def case_path(self, name: str, *, project: str | None = None) -> Path:
        """Return the filesystem path for the named case YAML file.

        This path is suitable for passing directly to ``load_raw_case_config``
        or ``ApplicationService.run_simulation``.  The case is not required to
        exist — callers can use this to check existence themselves.
        """
        self._validate_name(name)
        if project is not None:
            self._validate_project_name(project)
        return self._case_path(name, project=project)

    def exists(self, name: str, *, project: str | None = None) -> bool:
        """Return True if a case with the given name exists in the store."""
        self._validate_name(name)
        if project is not None:
            self._validate_project_name(project)
        return self._case_path(name, project=project).exists()

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
