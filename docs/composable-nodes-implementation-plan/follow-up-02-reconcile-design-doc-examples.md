# Follow-Up 2: Reconcile Design Doc Examples with Implementation

[Documentation](../index.md) › [Implementation Plan](index.md) › [Follow-Up Work](follow-up-work.md) › Follow-Up 2: Reconcile Design Doc Examples

**Status:** [ ] Not started

## Goal

Resolve documentation drift between `docs/composable-nodes-and-recipes.md` and the implemented recipe schema, validation rules, and registry examples.

## Scope

Primarily documentation. May require small schema or validation changes if the team chooses to implement the richer forms described in the design doc instead of updating examples.

## Background

The design doc contains aspirational examples that differ from current behavior:

| Design doc | Current implementation |
| --- | --- |
| `japanese_tokenization` capability | `tokenization` capability on `tokenization.kuromoji_tokenize` |
| `preferred_node` as object with `id` and `version` | `preferred_node` is a string; `version` is a sibling field on `select` |
| Compound version ranges such as `>=1.2,<2.0` | Single-operator constraints only (`>=`, `<=`, `>`, `<`, `==`) |

## Tasks

- [ ] Inventory every example in `docs/composable-nodes-and-recipes.md` that references capabilities, version constraints, or `preferred_node` shape.
- [ ] Decide the canonical approach for each drift item (see Decision Points below).
- [ ] Update design doc examples to match the chosen canonical forms.
- [ ] Cross-check against live registry artifacts:
  - `registry/recipes/opensearch-hybrid-index-japanese-chunk.json`
  - `registry/nodes/bpg-nodes-search.json`
  - `registry/nodes/opensearch.json`
- [ ] Add a short "Implemented today" note where the design doc describes future BPG behavior (locked execution plans, generated adapters).
- [ ] Link to [Follow-Up 4](follow-up-04-compound-version-constraints.md) and [Follow-Up 5](follow-up-05-structured-preferred-node-references.md) if those steps change the canonical forms.

## Decision Points

Choose one path per item and record the decision in the design doc or a brief note in this file's Delivered section:

1. **Capability naming** — Use `tokenization` (match registry) or introduce `japanese_tokenization` as a secondary capability tag.
2. **`preferred_node` shape** — Document string + sibling `version` as canonical, or implement the object form (see Follow-Up 5).
3. **Version constraints** — Document single-operator constraints only, or implement compound ranges (see Follow-Up 4).

## Acceptance Criteria

- No design doc example contradicts `schemas/recipe.schema.json` or `src/bpg_marketplace/validation.py` without an explicit "planned" or "future" label.
- Capability names in examples match the updated taxonomy (see Follow-Up 1).
- Version constraint examples are valid under the chosen grammar.
- `preferred_node` examples match the chosen schema shape.

## Dependencies

- [Follow-Up 1: Update Capability Taxonomy](follow-up-01-update-capability-taxonomy.md) — capability names should be settled first.
- [Follow-Up 4: Compound Version Constraints](follow-up-04-compound-version-constraints.md) — if compound ranges are implemented, update examples accordingly.
- [Follow-Up 5: Structured `preferred_node` References](follow-up-05-structured-preferred-node-references.md) — if the object form is adopted, update examples accordingly.

## Notes

Default recommendation from the audit: update the design doc to match the implemented schema unless BPG consumers already depend on the richer forms.

## References

- [Composable Nodes and Recipes](../composable-nodes-and-recipes.md)
- [Recipe schema](../../schemas/recipe.schema.json)
- [Validation logic](../../src/bpg_marketplace/validation.py)
