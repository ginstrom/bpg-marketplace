# Follow-Up 9: Assert Generated Index Reproducibility in CI

[Documentation](../index.md) › [Implementation Plan](index.md) › [Follow-Up Work](follow-up-work.md) › Follow-Up 9: Index Reproducibility in CI

**Status:** [ ] Not started

## Goal

Detect subtle indexer drift by verifying that `scripts/build_index.py` produces stable output across repeated runs.

## Scope

CI workflow and optionally a small helper script or test. No changes to index content unless a reproducibility bug is found.

## Background

`generated/*.json` is gitignored. CI runs `python scripts/build_index.py` once and checks for success, but does not verify that two consecutive builds produce identical output. Non-deterministic ordering, timestamps, or floating metadata could slip through.

## Tasks

- [ ] Inspect `src/bpg_marketplace/indexer.py` for known non-determinism (timestamps, unordered dict iteration, random IDs).
- [ ] Choose an approach:

  | Approach | Pros | Cons |
  | --- | --- | --- |
  | Double build in CI | No committed artifacts | Slightly longer CI |
  | Checksum manifest | Fast compare | Must update manifest on intentional index changes |

- [ ] Implement the chosen approach:

  **Option A — double build (recommended):**
  - [ ] Add a CI step that builds into two temp directories.
  - [ ] Compare outputs with `diff -r` or a small Python comparator.
  - [ ] Fail CI on any difference.

  **Option B — checksum manifest:**
  - [ ] Add `scripts/check_index_reproducibility.py` or extend `build_index.py` with a `--check` flag.
  - [ ] Store checksums in a committed manifest (for example `generated/.checksums.json` or `tests/fixtures/index-checksums.json`).
  - [ ] Update manifest when registry changes intentionally affect index output.

- [ ] Add a unit test that exercises reproducibility locally (optional but helpful for debugging).
- [ ] Document the CI check in `docs/contributing.md` (see Follow-Up 3).
- [ ] Run the new check locally and confirm it passes on a clean tree.

## Acceptance Criteria

- CI fails if two back-to-back index builds produce different file contents.
- The check runs after `pip install -e .` in the existing CI job (or a dedicated job).
- Intentional indexer changes can be merged by fixing the root cause or updating the checksum manifest (if Option B).
- No generated JSON is committed to the repository unless using a checksum manifest approach.

## Dependencies

- [Follow-Up 3: Expand Contributing Guidance](follow-up-03-expand-contributing-guidance.md) — document the new check.

## Notes

Prefer Option A (double build) to avoid committing generated artifacts or checksum files that require manual updates.

If index output intentionally includes a build timestamp, remove or normalize it in the indexer before adding this check.

## References

- [CI workflow](../../.github/workflows/ci.yml)
- [Build index script](../../scripts/build_index.py)
- [Indexer logic](../../src/bpg_marketplace/indexer.py)
- [Step 6: Index Recipes and Resolution Metadata](step-06-index-recipes-and-resolution-metadata.md)
