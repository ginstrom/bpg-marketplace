# Composable Nodes Follow-Up Work

[Documentation](../index.md) › [Implementation Plan](index.md) › Follow-Up Work

This plan captures remaining polish, documentation drift, and deferred enforcement identified during the composable nodes implementation audit.

The nine core implementation steps are complete and the marketplace foundation is sound. These follow-up items are not blockers.

Complete the checkboxes as work lands.

## Status Summary

| Area | State |
| --- | --- |
| Core plan (Steps 1–9) | Complete |
| Tests and CI | Passing |
| Registry validation and static verification | Passing |
| Index generation | Passing |
| Follow-up steps below | Open |

## Steps

### Documentation

- [x] [Follow-Up 1: Update Capability Taxonomy](follow-up-01-update-capability-taxonomy.md)
- [x] [Follow-Up 2: Reconcile Design Doc Examples with Implementation](follow-up-02-reconcile-design-doc-examples.md)
- [ ] [Follow-Up 3: Expand Contributing Guidance](follow-up-03-expand-contributing-guidance.md)

### Validation and Schema

- [x] [Follow-Up 4: Support Compound Version Constraints](follow-up-04-compound-version-constraints.md)
- [ ] [Follow-Up 5: Decide on Structured `preferred_node` References](follow-up-05-structured-preferred-node-references.md)
- [ ] [Follow-Up 6: Add an `external_service` Registry Example](follow-up-06-external-service-registry-example.md) — defer until a real external dependency is ready

### Test Coverage

- [ ] [Follow-Up 7: Test Node-Level Worker Override](follow-up-07-test-node-level-worker-override.md)
- [ ] [Follow-Up 8: Integration Tests for Remaining Transform Types](follow-up-08-integration-tests-transform-types.md)
- [ ] [Follow-Up 9: Assert Generated Index Reproducibility in CI](follow-up-09-index-reproducibility-ci.md)

### Verification

- [ ] [Follow-Up 10: Clarify Runtime-Light Verification Expectations](follow-up-10-runtime-light-verification-expectations.md)

## Suggested Order of Work

1. [Follow-Up 1](follow-up-01-update-capability-taxonomy.md) and [Follow-Up 2](follow-up-02-reconcile-design-doc-examples.md) — documentation, low risk.
2. [Follow-Up 3](follow-up-03-expand-contributing-guidance.md) — document the full local workflow.
3. [Follow-Up 4](follow-up-04-compound-version-constraints.md) — compound version support with tests; revisit Follow-Up 2 examples afterward.
4. [Follow-Up 5](follow-up-05-structured-preferred-node-references.md) — decide `preferred_node` shape; revisit Follow-Up 2 examples afterward.
5. [Follow-Up 7](follow-up-07-test-node-level-worker-override.md) and [Follow-Up 8](follow-up-08-integration-tests-transform-types.md) — test coverage.
6. [Follow-Up 9](follow-up-09-index-reproducibility-ci.md) — CI reproducibility check.
7. [Follow-Up 10](follow-up-10-runtime-light-verification-expectations.md) — verification usage documentation.
8. [Follow-Up 6](follow-up-06-external-service-registry-example.md) — when a real external dependency is available.

## Out of Scope (BPG Repository)

These items are noted for coordination but belong in BPG, not `bpg-marketplace`:

- Locked execution plan generation from `generated/resolution.json`
- Compilation of declarative mapping transforms into internal adapter operations
- Generated workflow/activity bindings
- Worker image digest pinning at build time
- `bpg marketplace verify` CLI wrapping the library API
- Optional BPG monorepo CI job running runtime-light against synced marketplace metadata

## References

- [Composable Nodes Implementation Plan](index.md)
- [Composable Nodes and Recipes](../composable-nodes-and-recipes.md)
- [Temporal Activity Adapter Expectations](../temporal-activity-adapters.md)
- [Capability Taxonomy](../capability-taxonomy.md)
