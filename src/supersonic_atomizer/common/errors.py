"""Runtime error classes.

These exceptions provide concrete error categories aligned with the approved
repository taxonomy. They are intentionally lightweight and category-focused.
"""

from __future__ import annotations


class SupersonicAtomizerError(Exception):
    """Base exception for repository-defined runtime errors."""


class InputParsingError(SupersonicAtomizerError):
    """Raised for failures while reading or parsing external inputs."""


class ConfigurationError(SupersonicAtomizerError):
    """Raised for structurally valid but invalid runtime configuration."""


class ModelSelectionError(SupersonicAtomizerError):
    """Raised for unsupported or unavailable model-selection requests."""


class ThermoError(SupersonicAtomizerError):
    """Raised for thermo-provider evaluation and validity failures."""


class NumericalError(SupersonicAtomizerError):
    """Raised for solver execution, closure, or state-update failures."""


class OutputError(SupersonicAtomizerError):
    """Raised for output serialization, path, or artifact write failures."""


class ValidationError(SupersonicAtomizerError):
    """Raised for validation execution or reporting failures."""