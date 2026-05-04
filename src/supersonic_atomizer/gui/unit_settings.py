"""Unit conversion definitions and helpers for GUI display (P24-T02).

All solver inputs and outputs remain in SI units throughout the application.
This module provides conversion factors and formatting helpers used *only*
at the GUI display boundary (Post tab plots and results table).

Architectural boundary (architecture.md, Appendix B.9):
- This module is the single source of truth for all unit-group definitions,
  conversion factors, and display-formatting helpers.
- No conversion logic shall appear in solver, domain, IO, plotting, or config
  modules.
- Conversion formula: display_value = si_value × scale + offset
  The offset is non-zero only for temperature (K → °C: offset = -273.15).

Usage example::

    from supersonic_atomizer.gui.unit_settings import convert_series, display_unit_label

    prefs = {"pressure": "kPa", "diameter": "μm"}
    kpa_values = convert_series(pa_values, "pressure", prefs)
    label = display_unit_label("pressure", prefs)   # → "kPa"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UnitSpec:
    """Immutable conversion specification for a single display unit.

    Parameters
    ----------
    label:
        Display label shown to the user, e.g. ``"kPa"``.
    scale:
        Multiply the SI value by this factor to get the display value.
    offset:
        Add this to ``si_value * scale`` to get the display value.
        Non-zero only for Celsius (offset = -273.15).
    """

    label: str
    scale: float
    offset: float = 0.0


# ── Unit group definitions ────────────────────────────────────────────────────

UNIT_GROUPS: dict[str, dict[str, UnitSpec]] = {
    "pressure": {
        "Pa":  UnitSpec("Pa",  1.0),
        "kPa": UnitSpec("kPa", 1e-3),
        "MPa": UnitSpec("MPa", 1e-6),
        "bar": UnitSpec("bar", 1e-5),
    },
    "temperature": {
        "K":   UnitSpec("K",  1.0,  0.0),
        "°C":  UnitSpec("°C", 1.0, -273.15),
    },
    "velocity": {
        "m/s": UnitSpec("m/s", 1.0),
    },
    "diameter": {
        "m":   UnitSpec("m",  1.0),
        "mm":  UnitSpec("mm", 1e3),
        "μm":  UnitSpec("μm", 1e6),
        "nm":  UnitSpec("nm", 1e9),
    },
    "length": {
        "m":   UnitSpec("m",   1.0),
        "mm":  UnitSpec("mm",  1e3),
        "cm":  UnitSpec("cm",  1e2),
    },
    "area": {
        "m²":  UnitSpec("m²",  1.0),
        "mm²": UnitSpec("mm²", 1e6),
        "cm²": UnitSpec("cm²", 1e4),
    },
    "density": {
        "kg/m³": UnitSpec("kg/m³", 1.0),
    },
    "viscosity": {
        "Pa·s": UnitSpec("Pa·s", 1.0),
    },
    "surface_tension": {
        "N/m": UnitSpec("N/m", 1.0),
    },
    "mass_flow": {
        "kg/s": UnitSpec("kg/s", 1.0),
    },
    "dimensionless": {
        "-": UnitSpec("-", 1.0),
        "%": UnitSpec("%", 100.0),
    },
    "spring_constant": {
        "N/m": UnitSpec("N/m", 1.0),
    },
    "damping": {
        "kg/s": UnitSpec("kg/s", 1.0),
    },
}

# Default display unit label for each group.
DEFAULT_UNITS: dict[str, str] = {
    "pressure":    "kPa",
    "temperature": "K",
    "velocity":    "m/s",
    "diameter":    "μm",
    "length":      "m",
    "area":        "m²",
    "density":     "kg/m³",
    "viscosity":   "Pa·s",
    "surface_tension": "N/m",
    "mass_flow":   "kg/s",
    "dimensionless": "-",
    "spring_constant": "N/m",
    "damping": "kg/s",
}

# Maps output-field names to their unit group.
# None means dimensionless — no conversion and no unit suffix.
FIELD_UNIT_GROUP: dict[str, Optional[str]] = {
    "x":                        "length",
    "A":                        "area",
    "pressure":                 "pressure",
    "temperature":              "temperature",
    "density":                  "density",
    "working_fluid_velocity":   "velocity",
    "Mach_number":              None,   # dimensionless
    "droplet_velocity":         "velocity",
    "slip_velocity":            "velocity",
    "droplet_mean_diameter":    "diameter",
    "droplet_maximum_diameter": "diameter",
    "Weber_number":             None,   # dimensionless
    "breakup_flag":             None,   # boolean flag
    "droplet_reynolds_number":  None,   # dimensionless
}

# ── Type alias ────────────────────────────────────────────────────────────────

UnitPreferences = dict[str, str]   # group_name → unit_label


# ── Low-level helpers ─────────────────────────────────────────────────────────


def get_unit_spec(group: str, unit_label: str) -> UnitSpec:
    """Return the :class:`UnitSpec` for *group* / *unit_label*.

    Raises
    ------
    KeyError
        If *group* or *unit_label* is unknown.
    """
    if group not in UNIT_GROUPS:
        raise KeyError(f"Unknown unit group: {group!r}")
    specs = UNIT_GROUPS[group]
    if unit_label not in specs:
        raise KeyError(f"Unknown unit {unit_label!r} for group {group!r}")
    return specs[unit_label]


def _resolve_spec(group: str, prefs: UnitPreferences) -> UnitSpec:
    """Return the UnitSpec for *group* using *prefs*, falling back to DEFAULT_UNITS."""
    unit_label = prefs.get(group, DEFAULT_UNITS.get(group, ""))
    return get_unit_spec(group, unit_label)


# ── Public conversion helpers ─────────────────────────────────────────────────


def convert_value(si_value: float, group: str, prefs: UnitPreferences) -> float:
    """Convert a single SI value to the display unit specified in *prefs*.

    Parameters
    ----------
    si_value:
        Value in SI units.
    group:
        Unit group name (e.g. ``"pressure"``).
    prefs:
        Mapping of group → selected unit label.
    """
    spec = _resolve_spec(group, prefs)
    return si_value * spec.scale + spec.offset


def convert_series(si_values: list[float], group: str, prefs: UnitPreferences) -> list[float]:
    """Convert a list of SI values to the display unit specified in *prefs*.

    Parameters
    ----------
    si_values:
        Values in SI units.
    group:
        Unit group name.
    prefs:
        Mapping of group → selected unit label.
    """
    spec = _resolve_spec(group, prefs)
    if spec.offset == 0.0:
        return [v * spec.scale for v in si_values]
    return [v * spec.scale + spec.offset for v in si_values]


def display_unit_label(group: str, prefs: UnitPreferences) -> str:
    """Return the display unit label for *group* (e.g. ``"kPa"``).

    Falls back to :data:`DEFAULT_UNITS` when the group is not in *prefs*.
    """
    return prefs.get(group, DEFAULT_UNITS.get(group, ""))


def field_display_label(field: str, prefs: UnitPreferences) -> str:
    """Return a human-readable axis / column label for *field*.

    Examples
    --------
    - ``"pressure"``    → ``"pressure [kPa]"`` (with kPa prefs)
    - ``"Mach_number"`` → ``"Mach_number"``    (dimensionless — no suffix)
    """
    group = FIELD_UNIT_GROUP.get(field)
    if group is None:
        return field
    unit = display_unit_label(group, prefs)
    return f"{field} [{unit}]"
