# Composable Nodes Implementation Plan

This plan breaks [Composable Nodes and Recipes](../composable-nodes-and-recipes.md) into self-contained implementation steps.

Each step is intended to be small enough to hand to an engineer. Complete the checkboxes as work lands.

## Steps

- [x] [Step 1: Add Recipe Registry Support](step-01-recipe-registry.md)
- [x] [Step 2: Extend Node Metadata Schema](step-02-node-metadata-schema.md)
- [x] [Step 3: Add Sample Atomic Search Nodes](step-03-sample-search-nodes.md)
- [x] [Step 4: Add Japanese Hybrid Indexing Recipe](step-04-japanese-hybrid-indexing-recipe.md)
- [x] [Step 5: Add Declarative Edge Mappings and Adapter Semantics](step-05-declarative-edge-mappings.md)
- [x] [Step 6: Index Recipes and Resolution Metadata](step-06-index-recipes-and-resolution-metadata.md)
- [x] [Step 7: Validate References and Schema Compatibility](step-07-reference-and-schema-validation.md)
- [x] [Step 8: Add Lightweight Runtime Verification](step-08-lightweight-runtime-verification.md)
- [x] [Step 9: Document Temporal Activity Adapter Expectations](step-09-temporal-activity-adapters.md)

## Follow-Up Work

Remaining polish, documentation drift, and deferred enforcement from the implementation audit. See [Follow-Up Work](follow-up-work.md) for the full index.

### Documentation

- [x] [Follow-Up 1: Update Capability Taxonomy](follow-up-01-update-capability-taxonomy.md)
- [x] [Follow-Up 2: Reconcile Design Doc Examples](follow-up-02-reconcile-design-doc-examples.md)
- [x] [Follow-Up 3: Expand Contributing Guidance](follow-up-03-expand-contributing-guidance.md)

### Validation and Schema

- [x] [Follow-Up 4: Compound Version Constraints](follow-up-04-compound-version-constraints.md)
- [x] [Follow-Up 5: Structured `preferred_node` References](follow-up-05-structured-preferred-node-references.md)
- [ ] [Follow-Up 6: `external_service` Registry Example](follow-up-06-external-service-registry-example.md)

### Test Coverage and Verification

- [ ] [Follow-Up 7: Node-Level Worker Override Tests](follow-up-07-test-node-level-worker-override.md)
- [ ] [Follow-Up 8: Transform Type Integration Tests](follow-up-08-integration-tests-transform-types.md)
- [ ] [Follow-Up 9: Index Reproducibility in CI](follow-up-09-index-reproducibility-ci.md)
- [ ] [Follow-Up 10: Runtime-Light Verification Expectations](follow-up-10-runtime-light-verification-expectations.md)

## Expected End State

After these steps, the marketplace should support:

- `recipe` artifacts in the registry.
- Versioned node references and capability-based recipe selectors.
- Runtime metadata for Temporal activities, service containers, external services, workers, IO schemas, and dependencies.
- Build-time inputs that BPG can turn into locked execution plans.
- Declarative edge mappings for simple output-to-input adaptation, with internal plan adapters generated only when needed.
- Lightweight authoring checks that can run in marketplace CI or from BPG.
- CI coverage that validates ignored generated index files can be rebuilt from checked-in registry metadata.
