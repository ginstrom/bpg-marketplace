# Step 7: Validate References and Schema Compatibility

## Goal

Add validation beyond JSON Schema so authored recipes and nodes can be checked before publication and before [BPG](https://github.com/ginstrom/bpg) plan generation.

## Scope

This step adds static validation for references, version constraints, JSONPath mappings, declarative mapping transforms, and IO schema compatibility. It does not import Python entrypoints or check container availability.

## Tasks

1. Validate exact recipe node references.
2. Validate recipe node version constraints.
3. Validate `preferred_node` references when present.
4. Validate step references in JSONPath mappings.
5. Validate that mappings only reference declared recipe inputs or prior step outputs.
6. Validate that referenced IO schema files exist.
7. Validate supported declarative mapping transform types.
8. Validate basic compatibility between mapped output fields and target input fields.
9. Add tests for invalid references, invalid versions, bad JSONPath mappings, unsupported transforms, and incompatible schemas.

## Compatibility Rules

Use conservative initial rules:

- A step may only read recipe inputs or outputs from earlier steps.
- JSONPath must use the [BPG](https://github.com/ginstrom/bpg)-supported subset.
- Exact node references must resolve to at least one node version.
- Version constraints must resolve to at least one compatible version.
- Mapped fields must exist in the source schema when source schema metadata is available.
- Target input fields marked required must be supplied by the step mapping or defaults.
- Simple projection transforms such as array-object-to-array-string are valid when the projected field type matches the target item type.

## Acceptance Criteria

- A recipe that references an unknown node fails validation.
- A recipe that references a future step output fails validation.
- A recipe with an impossible version constraint fails validation.
- A recipe step missing a required node input fails validation.
- A recipe with an unsupported mapping transform fails validation.
- A recipe with an incompatible projection transform fails validation.
- Validation output identifies the recipe, step, and field that failed.

## Notes

This validation is a precursor to [BPG](https://github.com/ginstrom/bpg)'s build-time enforcement. Marketplace validation should make authoring errors cheap to catch, while [BPG](https://github.com/ginstrom/bpg) remains the final authority for environment-specific compatibility.
