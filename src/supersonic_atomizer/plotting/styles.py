"""Central plotting labels and default style helpers."""

from __future__ import annotations


PLOT_LABELS: dict[str, tuple[str, str]] = {
	"pressure": ("Pressure", "pressure [Pa]"),
	"temperature": ("Temperature", "temperature [K]"),
	"working_fluid_velocity": ("Working Fluid Velocity", "velocity [m/s]"),
	"droplet_velocity": ("Droplet Velocity", "velocity [m/s]"),
	"mach_number": ("Mach Number", "Mach number [-]"),
	"droplet_mean_diameter": ("Droplet Mean Diameter", "diameter [m]"),
	"droplet_maximum_diameter": ("Droplet Maximum Diameter", "diameter [m]"),
	"weber_number": ("Weber Number", "Weber number [-]"),
}