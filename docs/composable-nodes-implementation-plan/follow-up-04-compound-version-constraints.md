# Follow-Up 4: Support Compound Version Constraints

[Documentation](../index.md) › [Implementation Plan](index.md) › [Follow-Up Work](follow-up-work.md) › Follow-Up 4: Compound Version Constraints

**Status:** [ ] Not started

## Goal

Extend version constraint parsing so recipe selectors can express compound ranges such as `>=1.2,<2.0` instead of treating them as opaque literal strings.

## Scope

Validation logic and tests. Schema documentation updates if the supported grammar needs to be written down.

## Background

`_version_matches` in `src/bpg_marketplace/validation.py` handles a single operator per constraint. Compound constraints shown in `docs/composable-nodes-and-recipes.md` fall through to string equality and will not resolve nodes correctly.

## Tasks

- [ ] Define the supported constraint grammar (recommended: comma-separated clauses, each with one of `>=`, `<=`, `>`, `<`, `==`, `=`).
- [ ] Document the grammar in `docs/composable-nodes-and-recipes.md` or a short comment in `validation.py`.
- [ ] Implement compound parsing in `_version_matches`:
  - Split on commas (with whitespace tolerance).
  - Require every clause to match for the constraint to pass.
  - Preserve backward compatibility for single-operator and exact-match constraints.
- [ ] Handle edge cases:
  - Empty or whitespace-only constraint (match all).
  - Invalid clause syntax (fail validation with a clear message).
  - Pre-release suffixes on versions (`1.2.0-beta`) using existing `_parse_version` behavior.
- [ ] Add positive tests in `tests/test_validation.py`:
  - `>=1.2,<2.0` matches `1.2.0`, `1.9.9`, rejects `2.0.0` and `1.1.0`.
  - Single-operator constraints still work.
  - Exact string match still works when parsing fails.
- [ ] Add negative tests for malformed compound constraints.
- [ ] Run full test suite and `python3 scripts/validate_registry.py`.
- [ ] Update [Follow-Up 2](follow-up-02-reconcile-design-doc-examples.md) design doc examples if this step lands first.

## Acceptance Criteria

- `_version_matches("1.5.0", ">=1.2,<2.0")` returns `True`.
- `_version_matches("2.0.0", ">=1.2,<2.0")` returns `False`.
- Existing single-operator tests continue to pass.
- Recipe validation reports a clear error for unparseable compound constraints.
- `python3 -m unittest discover -s tests` passes.

## Dependencies

- None required. Informs [Follow-Up 2](follow-up-02-reconcile-design-doc-examples.md) if design doc examples use compound ranges.

## Notes

Do not implement full semver range syntax (npm-style carets, OR clauses) unless explicitly needed. Start with comma-separated AND clauses to match existing design doc examples.

## References

- [Validation logic](../../src/bpg_marketplace/validation.py) — `_version_matches`, `_parse_version`
- [Tests](../../tests/test_validation.py)
- [Composable Nodes and Recipes](../composable-nodes-and-recipes.md)
