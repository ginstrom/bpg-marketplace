# Follow-Up 7: Test Node-Level Worker Override

[Documentation](../index.md) › [Implementation Plan](index.md) › [Follow-Up Work](follow-up-work.md) › Follow-Up 7: Node-Level Worker Override Tests

**Status:** [ ] Not started

## Goal

Add dedicated test coverage proving that node-level `worker` declarations override package-level defaults during validation and index generation.

## Scope

Tests only. No production logic changes unless a bug is discovered.

## Background

Step 2 acceptance criteria require node-level worker overrides. `opensearch.service` in `registry/nodes/opensearch.json` declares a node-level `worker` block, and `tests/test_indexer.py` asserts some worker fields in resolution output, but no test explicitly validates the override semantics against a package default.

## Tasks

- [ ] Review `opensearch.service` and its parent package for package-level vs node-level `worker` fields.
- [ ] Add a validation test in `tests/test_validation.py` that:
  - [ ] Uses an inline or fixture node package with both package-level and node-level `worker` blocks.
  - [ ] Asserts validation accepts the node.
  - [ ] Asserts node-level fields take precedence where they differ (for example `task_queue`, `image`, `install_mode`).
- [ ] Add an indexer test in `tests/test_indexer.py` that:
  - [ ] Builds resolution output for the override node.
  - [ ] Asserts `generated/resolution.json`-shaped output preserves node-level worker values, not package defaults.
- [ ] Optionally extend the existing `opensearch.service` assertions rather than adding synthetic fixtures, if that keeps tests maintainable.
- [ ] Run `python3 -m unittest discover -s tests -v`.

## Acceptance Criteria

- A test fails if node-level `worker` values are silently replaced by package defaults in index output.
- Validation continues to accept valid node-level overrides.
- Tests name the override behavior explicitly (test method docstring or comment).
- Full test suite passes.

## References

- [Step 2: Extend Node Metadata Schema](step-02-node-metadata-schema.md)
- [OpenSearch node package](../../registry/nodes/opensearch.json)
- [Indexer tests](../../tests/test_indexer.py)
- [Indexer logic](../../src/bpg_marketplace/indexer.py)
