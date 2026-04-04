"""Raw configuration loading.

This module owns file access and raw external parse entry only.
It must not perform schema validation, semantic validation, default application,
translation into internal models, or solver work.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_raw_case_config(case_path: str | Path) -> dict[str, Any]:
    """Load one YAML case file into a raw external configuration mapping.

    Parameters
    ----------
    case_path:
        Path to the case file to read.

    Returns
    -------
    dict[str, Any]
        Raw parsed YAML content represented as an external mapping.

    Raises
    ------
    FileNotFoundError
        If the requested case file does not exist.
    ValueError
        If the file cannot be parsed as valid YAML or does not contain a
        top-level mapping structure.
    """

    resolved_path = Path(case_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Case file does not exist: {resolved_path}")

    try:
        raw_content = resolved_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Unable to read case file: {resolved_path}") from exc

    try:
        parsed = yaml.safe_load(raw_content)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML syntax in case file: {resolved_path}") from exc

    if not isinstance(parsed, dict):
        raise ValueError(
            "Case file must contain a top-level mapping structure."
        )

    return parsed