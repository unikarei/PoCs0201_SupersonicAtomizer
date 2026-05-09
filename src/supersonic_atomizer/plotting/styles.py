"""Central plotting labels and default style helpers."""

from __future__ import annotations


PLOT_LABELS: dict[str, tuple[str, str]] = {
	"pressure": ("Static Pressure", "static pressure [Pa]"),
	"temperature": ("Temperature", "temperature [K]"),
	"working_fluid_velocity": ("Working Fluid Velocity", "velocity [m/s]"),
	"droplet_velocity": ("Droplet Velocity", "velocity [m/s]"),
	"mach_number": ("Mach Number", "Mach number [-]"),
	"droplet_mean_diameter": ("Droplet Mean Diameter", "diameter [m]"),
	"droplet_maximum_diameter": ("Droplet Maximum Diameter", "diameter [m]"),
	"weber_number": ("Weber Number", "Weber number [-]"),
	"area_profile": ("Area Profile", "area [m^2]"),
	"slip_velocity": ("Slip Velocity", "velocity [m/s]"),
	"pressure_over_total": ("Pressure / Inlet total pressure", "-"),
}