# Follow-Up 10: Clarify Runtime-Light Verification Expectations

[Documentation](../index.md) › [Implementation Plan](index.md) › [Follow-Up Work](follow-up-work.md) › Follow-Up 10: Runtime-Light Verification Expectations

**Status:** [ ] Not started

## Goal

Document when and where to run `runtime-light` verification so marketplace, node package, and BPG engineers share the same expectations.

## Scope

Documentation. Optional cross-repo CI note for the BPG monorepo (out of repo changes unless explicitly requested).

## Background

Runtime-light verification is implemented in `src/bpg_marketplace/verification.py` and tested with dummy entrypoints in `tests/test_verification.py`. Marketplace CI runs `--mode static` only because node packages (`bpg_nodes_search`, `bpg_nodes_opensearch`, etc.) are not installed in this repository.

Running `python3 scripts/verify_registry.py --mode runtime-light` locally without those packages correctly reports import failures — that is expected behavior, not a marketplace bug.

## Tasks

- [ ] Add a "Verification modes" section to `docs/temporal-activity-adapters.md` or a dedicated subsection in `docs/contributing.md`.
- [ ] Document the intended usage model:

  | Context | Mode | Notes |
  | --- | --- | --- |
  | Marketplace CI | `static` | Validates metadata, schemas, image references, entrypoint strings |
  | Node package repo CI | `runtime-light` | Run after `pip install` of the package; imports entrypoints |
  | BPG build flow | `runtime-light` or stricter | Packages available in build environment |
  | Local authoring | `static` always; `runtime-light` when package installed | See commands below |

- [ ] Document expected local commands:

  ```bash
  # Always run in marketplace and node repos
  python3 scripts/verify_registry.py --mode static

  # Run in node package repo after install
  pip install -e .
  python3 scripts/verify_registry.py --mode runtime-light
  ```

- [ ] Explain what runtime-light checks:
  - [ ] Python entrypoint importability.
  - [ ] Entrypoint callable shape (if implemented).
  - [ ] Differences from static mode (no import required for static).
- [ ] Note that import failures in the marketplace repo alone are expected.
- [ ] Cross-link from [Follow-Up 3: Expand Contributing Guidance](follow-up-03-expand-contributing-guidance.md).
- [ ] Optionally add a short "Future work" note about a BPG monorepo CI job that syncs marketplace metadata and runs runtime-light with all packages installed.

## Acceptance Criteria

- A node package author understands they must run runtime-light in their own repo, not rely on marketplace CI.
- A marketplace contributor understands why CI uses static mode only.
- Documentation is linked from `docs/index.md` (via Contributing or Temporal Activity Adapters).
- No misleading implication that marketplace CI failures on runtime-light are bugs.

## Out of Scope (BPG Repository)

These belong in BPG coordination, not `bpg-marketplace`:

- `bpg marketplace verify` CLI wrapping the library API
- Monorepo CI job running runtime-light against all synced packages

Record these in [Follow-Up Work](follow-up-work.md) under Out of Scope if not already listed.

## References

- [Temporal Activity Adapter Expectations](../temporal-activity-adapters.md)
- [Step 8: Lightweight Runtime Verification](step-08-lightweight-runtime-verification.md)
- [Verification logic](../../src/bpg_marketplace/verification.py)
- [Verification tests](../../tests/test_verification.py)
- [Verify registry script](../../scripts/verify_registry.py)
