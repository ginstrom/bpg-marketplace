# Follow-Up 1: Update Capability Taxonomy

[Documentation](../index.md) › [Implementation Plan](index.md) › [Follow-Up Work](follow-up-work.md) › Follow-Up 1: Update Capability Taxonomy

**Status:** [x] Complete

## Goal

Bring `docs/capability-taxonomy.md` in line with capabilities declared in the live registry so authors and recipe selectors use a single, accurate vocabulary.

## Scope

Documentation only. No schema or validation changes.

## Background

The taxonomy currently lists audit and workflow capabilities but omits search and indexing capabilities that are already in use by sample node packages and recipes.

## Tasks

- [ ] Audit `registry/nodes/` and `registry/recipes/` for all declared `capabilities` values.
- [ ] Add missing search and indexing capabilities to `docs/capability-taxonomy.md`, including at minimum:
  - `embedding`
  - `tokenization`
  - `hybrid_upsert`
  - `bm25_search`
- [ ] Add brief one-line descriptions for each capability where helpful.
- [ ] Note any capabilities that are registry-only aliases or deprecated in favor of another term.
- [ ] Link the taxonomy from `docs/composable-nodes-and-recipes.md` if not already referenced in the capability-selection section.
- [ ] Run `python3 scripts/validate_registry.py` to confirm no registry drift was introduced (documentation-only change).

## Acceptance Criteria

- Every capability referenced by a checked-in recipe or node package appears in `docs/capability-taxonomy.md` or is explicitly marked deprecated with a replacement.
- The four search/indexing capabilities above are documented.
- `docs/index.md` continues to link to the taxonomy.

## Notes

Keep capability names concise and machine-readable. Prefer updating the taxonomy when new node packages land rather than letting it drift again.

## References

- [Capability Taxonomy](../capability-taxonomy.md)
- [Follow-Up Work index](follow-up-work.md)
- [Step 3: Add Sample Atomic Search Nodes](step-03-sample-search-nodes.md)
