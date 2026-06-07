# Follow-Up 5: Decide on Structured `preferred_node` References

[Documentation](../index.md) › [Implementation Plan](index.md) › [Follow-Up Work](follow-up-work.md) › Follow-Up 5: Structured `preferred_node` References

**Status:** [x] Complete

## Delivered

Documented the string + sibling `version` form as canonical in `docs/composable-nodes-and-recipes.md`. No schema changes required.

## Goal

Resolve the mismatch between the design doc's object-shaped `preferred_node` examples and the implemented string + sibling `version` pattern.

## Scope

Decision and documentation, with optional schema and validation changes if the object form is adopted.

## Background

`docs/composable-nodes-and-recipes.md` shows:

```json
"preferred_node": {
  "id": "tokenization.kuromoji_tokenize",
  "version": ">=1.2,<2.0"
}
```

The recipe schema and validator accept only:

```json
"preferred_node": "tokenization.kuromoji_tokenize",
"version": ">=1.2,<2.0"
```

Live registry recipes use the string form (see `registry/recipes/opensearch-hybrid-index-japanese-chunk.json`).

## Tasks

- [ ] Confirm no downstream [BPG](https://github.com/ginstrom/bpg) consumer requires the object form.
- [ ] Choose one canonical approach (see Options below).
- [ ] If **document string form**:
  - [ ] Update design doc examples.
  - [ ] Add a short rationale in `docs/composable-nodes-and-recipes.md` (simpler schema, mirrors `select.node` + `select.version`).
  - [ ] Mark this step complete without schema changes.
- [ ] If **implement object form**:
  - [ ] Extend `schemas/recipe.schema.json` to accept either a string or `{ "id": string, "version": string }`.
  - [ ] Update validation in `src/bpg_marketplace/validation.py` to normalize both shapes.
  - [ ] Update indexer if resolution output should canonicalize to one shape.
  - [ ] Add tests for both accepted forms and rejection of invalid objects.
  - [ ] Migrate or allow both forms in existing registry recipes.
- [ ] Update [Follow-Up 2](follow-up-02-reconcile-design-doc-examples.md) once the decision is recorded.

## Options

| Option | Effort | Recommendation |
| --- | --- | --- |
| Document string + sibling `version` as canonical | Low | Preferred unless [BPG](https://github.com/ginstrom/bpg) requires object form |
| Support both shapes in schema and validation | Medium | Only if backward compatibility with unpublished design doc consumers is needed |
| Object form only | High | Not recommended; breaks existing registry recipes |

## Acceptance Criteria

- The canonical `preferred_node` shape is documented in `docs/composable-nodes-and-recipes.md`.
- Recipe validation behavior matches the documented shape(s).
- All checked-in registry recipes validate successfully.
- Tests cover the chosen shape(s).

## Dependencies

- [Follow-Up 4: Compound Version Constraints](follow-up-04-compound-version-constraints.md) — if `version` inside a `preferred_node` object uses compound ranges.
- [Follow-Up 2: Reconcile Design Doc Examples](follow-up-02-reconcile-design-doc-examples.md) — update after this decision.

## Notes

Default recommendation: document the string form. The registry already uses it consistently and the indexer preserves it in `generated/resolution.json`.

## References

- [Recipe schema](../../schemas/recipe.schema.json)
- [Validation logic](../../src/bpg_marketplace/validation.py)
- [Japanese hybrid indexing recipe](../../registry/recipes/opensearch-hybrid-index-japanese-chunk.json)
