# Air Thermo Provider Responsibilities

This document describes responsibilities and expectations for the air thermo provider implementation.

- The air provider must implement the `ThermoProvider` interface and provide density, sound speed, enthalpy, and other required properties consistent with SI units.
- Document expected supported states and any limitations of the air model.

Include examples of typical queries and expected units for returned values.

- The MVP air provider may use an **ideal gas** approximation for the supported state range.
- The provider should surface **nonphysical** state errors (negative density, invalid temperature) via the thermo interface failures.
- Document how the provider implements the shared **thermo interface** used by the gas solver and callers.
