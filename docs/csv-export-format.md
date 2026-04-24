# CSV Export Format

This document describes the CSV column order, names, and units for tabular exports.

Required columns include `x`, `A`, `pressure`, `temperature`, `density`, `working_fluid_velocity`, `Mach_number`, `droplet_velocity`, `droplet_mean_diameter`, `droplet_maximum_diameter`, and `Weber_number`.

There is a **stable documented column order** that writers must preserve for regression and downstream parsing.

Typical header example: x, A, pressure, temperature, density, working_fluid_velocity, Mach_number, droplet_velocity, droplet_mean_diameter, droplet_maximum_diameter, Weber_number

Example CSV files should label units in headers where relevant.

Output writers should follow the project's **run-artifact conventions** for naming and directory layout so CSV artifacts are discoverable and consistent across runs.