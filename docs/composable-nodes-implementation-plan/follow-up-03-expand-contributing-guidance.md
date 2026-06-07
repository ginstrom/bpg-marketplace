# Follow-Up 3: Expand Contributing Guidance

[Documentation](../index.md) › [Implementation Plan](index.md) › [Follow-Up Work](follow-up-work.md) › Follow-Up 3: Expand Contributing Guidance

**Status:** [x] Complete

## Goal

Document the full composable-nodes authoring workflow in `docs/contributing.md` so contributors know which checks to run locally and when.

## Scope

Documentation only. No CI or script changes unless a missing command reference is discovered.

## Background

`docs/contributing.md` lists tests, validation, and index building but omits static verification, runtime-light verification, and links to Temporal activity adapter guidance.

## Tasks

- [ ] Expand the Local Workflow section to include the full check sequence:

  ```bash
  python3 -m unittest discover -s tests
  python3 scripts/validate_registry.py
  python3 scripts/verify_registry.py --mode static
  python3 scripts/build_index.py
  ```

- [ ] Add a "When to run each check" subsection:

  | Check | When |
  | --- | --- |
  | Unit tests | After any Python change to validation, indexing, or verification |
  | `validate_registry.py` | After any registry or schema change |
  | `verify_registry.py --mode static` | After node metadata, image, or entrypoint reference changes |
  | `build_index.py` | After registry changes that affect discovery or resolution output |
  | `verify_registry.py --mode runtime-light` | After installing the node package locally (see Follow-Up 10) |

- [ ] Link to `docs/temporal-activity-adapters.md` for node package authors adding `temporal_activity` nodes.
- [ ] Link to `docs/composable-nodes-implementation-plan/index.md` and [Follow-Up Work](follow-up-work.md) for broader context.
- [ ] Link to `examples/node-authoring/sample-greet-node/` as a minimal authoring reference.
- [ ] Confirm commands match `.github/workflows/ci.yml` (CI uses `python` after setup; local docs use `python3`).

## Acceptance Criteria

- A new contributor can follow `docs/contributing.md` end-to-end without reading CI workflow source.
- Static verification is documented as part of the standard local workflow.
- Runtime-light verification is documented as optional and package-install-dependent.
- `docs/index.md` link to Contributing remains accurate.

## Notes

Keep the contributing guide concise. Point to specialized docs for Temporal adapter details rather than duplicating them.

## References

- [Contributing](../contributing.md)
- [Temporal Activity Adapter Expectations](../temporal-activity-adapters.md)
- [CI workflow](../../.github/workflows/ci.yml)
- [Follow-Up 10: Runtime-Light Verification Expectations](follow-up-10-runtime-light-verification-expectations.md)
