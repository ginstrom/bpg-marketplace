# Follow-Up 8: Integration Tests for Remaining Transform Types

[Documentation](../index.md) › [Implementation Plan](index.md) › [Follow-Up Work](follow-up-work.md) › Follow-Up 8: Transform Type Integration Tests

**Status:** [ ] Not started

## Goal

Add test coverage for `project`, `default`, and `coerce` declarative mapping transforms so all supported transform types are exercised beyond the `map` transform used in the Japanese hybrid indexing recipe.

## Scope

Tests and minimal recipe fixtures. No schema changes unless gaps are found.

## Background

Step 5 introduced four transform types: `project`, `map`, `default`, and `coerce`. `tests/test_validation.py` includes rejection tests for invalid transform types and incompatible projections, but only `map` is validated end-to-end via `registry/recipes/opensearch-hybrid-index-japanese-chunk.json`.

## Tasks

- [ ] Add unit tests in `tests/test_validation.py` for each transform type:

  | Transform | Test scenario |
  | --- | --- |
  | `project` | Extract a single field from a step output object into a scalar recipe input |
  | `default` | Source JSONPath absent or null; mapping supplies fallback value |
  | `coerce` | Scalar type conversion (for example integer to string, string to number) into a compatible input field |

- [ ] For each test, define minimal inline recipe fixtures with:
  - [ ] A prior step output schema shape in the test harness or a tiny mock node reference.
  - [ ] A `with` mapping using the transform under test.
  - [ ] Assertions that validation accepts valid mappings and rejects incompatible ones.
- [ ] Optionally add a small recipe fixture under `registry/recipes/` if a realistic example aids documentation (keep it minimal).
- [ ] Confirm `_validate_recipe_mapping_transform` and `_apply_transform_schema` paths are hit for each type.
- [ ] Run `python3 -m unittest discover -s tests -v` and `python3 scripts/validate_registry.py`.

## Example Fixtures

**`project`:**

```json
"document_id": {
  "from": "$.steps.ingest.document",
  "transform": {
    "type": "project",
    "path": "$.id"
  }
}
```

**`default`:**

```json
"locale": {
  "from": "$.inputs.locale",
  "transform": {
    "type": "default",
    "value": "ja-JP"
  }
}
```

**`coerce`:**

```json
"shard_count": {
  "from": "$.inputs.shards",
  "transform": {
    "type": "coerce",
    "to": "string"
  }
}
```

Adjust fixture shapes to match actual schema validation rules in `src/bpg_marketplace/validation.py`.

## Acceptance Criteria

- Each of `project`, `default`, and `coerce` has at least one positive validation test.
- Each transform type has at least one negative test (wrong source type, missing required transform field, or incompatible target input).
- Existing `map` transform coverage remains intact.
- Full test suite passes.

## References

- [Step 5: Declarative Edge Mappings](step-05-declarative-edge-mappings.md)
- [Validation logic](../../src/bpg_marketplace/validation.py)
- [Japanese hybrid indexing recipe](../../registry/recipes/opensearch-hybrid-index-japanese-chunk.json)
- [Validation tests](../../tests/test_validation.py)
