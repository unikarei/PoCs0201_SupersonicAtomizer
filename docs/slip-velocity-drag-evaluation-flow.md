# Slip Velocity and Drag Evaluation Flow

This document describes the slip-velocity calculation and drag evaluation flow used by the droplet solver.

Required sections:

- **Gas-State Lookup**
- **Slip-Velocity Evaluation**
- **Drag Input Preparation**: prepare local Reynolds number, droplet size, and relative velocity for the drag model.

Provide equations, required inputs, and expected timing relative to the droplet update sequence.

Final step: **Droplet Motion Update** where computed drag accelerations are applied to update droplet velocity and position metrics.

- The flow makes explicit use of both gas velocity and droplet velocity when computing relative velocities used in drag calculations (gas velocity and droplet velocity).