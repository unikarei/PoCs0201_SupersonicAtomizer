# Config Translation Flow

Placeholder describing raw YAML → schema validation → semantic validation → internal models.

The configuration processing flow proceeds through these stages:

1. **raw parse**: parse YAML into an in-memory raw structure.
2. **schema validation**: ensure required sections and field presence.
3. **semantic validation**: check physical and structural constraints.
4. **defaults application**: apply centralized default values to missing optional fields.
5. **translation into internal models**: map validated data into typed runtime case models.

Each stage is separate and produces explicit errors or warnings when validation fails.