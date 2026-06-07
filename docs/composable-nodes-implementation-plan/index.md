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
- [ ] [Step 7: Validate References and Schema Compatibility](step-07-reference-and-schema-validation.md)
- [ ] [Step 8: Add Lightweight Runtime Verification](step-08-lightweight-runtime-verification.md)
- [ ] [Step 9: Document Temporal Activity Adapter Expectations](step-09-temporal-activity-adapters.md)

## Expected End State

After these steps, the marketplace should support:

- `recipe` artifacts in the registry.
- Versioned node references and capability-based recipe selectors.
- Runtime metadata for Temporal activities, service containers, external services, workers, IO schemas, and dependencies.
- Build-time inputs that BPG can turn into locked execution plans.
- Declarative edge mappings for simple output-to-input adaptation, with internal plan adapters generated only when needed.
- Lightweight authoring checks that can run in marketplace CI or from BPG.
- CI coverage that validates ignored generated index files can be rebuilt from checked-in registry metadata.
