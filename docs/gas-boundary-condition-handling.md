# Gas Boundary Condition Handling

This document describes handling of inlet total conditions and outlet static pressure in the gas solver.

Key boundary keys include `Pt_in`, `Tt_in`, and `Ps_out`.

The config layer must detect **invalid or contradictory boundary combinations** (for example, nonphysical Pt_in/Ps_out pairs) and surface clear errors.

The marching solver uses inlet total conditions and the specified `Ps_out` to select an internal branch and perform axial assembly.

Note: the term **inlet total pressure** refers to the boundary value `Pt_in` supplied in the case YAML.