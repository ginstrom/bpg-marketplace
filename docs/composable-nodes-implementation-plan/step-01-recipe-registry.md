# Step 1: Add Recipe Registry Support

## Goal

Add first-class `recipe` artifacts to the marketplace registry without changing node or template behavior.

## Scope

This step introduces the artifact type, storage location, schema, loading, and basic validation. It does not implement execution planning or recipe reference validation beyond JSON Schema.

## Tasks

1. Create `registry/recipes/`.
2. Add `schemas/recipe.schema.json`.
3. Extend registry discovery so `recipe` artifacts are loaded alongside existing artifact types.
4. Extend validation so every file in `registry/recipes/` is checked against `schemas/recipe.schema.json`.
5. Update tests for registry loading and validation.
6. Update documentation that lists supported artifact types.

## Schema Requirements

The first recipe schema should support:

- `id`
- `type`, fixed to `recipe`
- `name`
- `summary`
- `version`
- `capabilities`
- `inputs`
- `outputs`
- `steps`
- `defaults`
- `failure_policy`
- `tradeoffs`

Each step should support:

- `id`
- `select.capability`
- `select.node`
- `select.preferred_node`
- `select.version`
- `with`
- `optional`

Only one of `select.capability` or `select.node` should be required for each step. `select.preferred_node` is only meaningful when `select.capability` is present.

## Acceptance Criteria

- `python3 -m unittest discover -s tests` passes or only fails for a clearly unrelated pre-existing issue.
- Invalid recipe JSON is rejected by validation.
- A minimal valid recipe can be added under `registry/recipes/`.
- Existing node and template artifacts still load as before.

## Notes

Keep this step schema-focused. Do not add a full workflow language. The recipe model should remain structured intent for later BPG build-time resolution.

