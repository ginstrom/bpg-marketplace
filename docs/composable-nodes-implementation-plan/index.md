# Composable Nodes Implementation Plan

This plan breaks [Composable Nodes and Recipes](../composable-nodes-and-recipes.md) into self-contained implementation steps.

Each step is intended to be small enough to hand to an engineer. Complete the checkboxes as work lands.

## Steps

- [x] [Step 1: Add Recipe Registry Support](step-01-recipe-registry.md)
- [ ] [Step 2: Extend Node Metadata Schema](step-02-node-metadata-schema.md)
- [ ] [Step 3: Add Sample Atomic Search Nodes](step-03-sample-search-nodes.md)
- [ ] [Step 4: Add Japanese Hybrid Indexing Recipe](step-04-japanese-hybrid-indexing-recipe.md)
- [ ] [Step 5: Index Recipes and Resolution Metadata](step-05-index-recipes-and-resolution-metadata.md)
- [ ] [Step 6: Validate References and Schema Compatibility](step-06-reference-and-schema-validation.md)
- [ ] [Step 7: Add Lightweight Runtime Verification](step-07-lightweight-runtime-verification.md)
- [ ] [Step 8: Document Temporal Activity Adapter Expectations](step-08-temporal-activity-adapters.md)

## Expected End State

After these steps, the marketplace should support:

- `recipe` artifacts in the registry.
- Versioned node references and capability-based recipe selectors.
- Runtime metadata for Temporal activities, service containers, external services, workers, IO schemas, and dependencies.
- Build-time inputs that BPG can turn into locked execution plans.
- Lightweight authoring checks that can run in marketplace CI or from BPG.
