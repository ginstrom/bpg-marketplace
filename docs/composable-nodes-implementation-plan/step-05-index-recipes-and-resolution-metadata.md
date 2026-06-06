# Step 5: Index Recipes and Resolution Metadata

## Goal

Update generated marketplace indexes so BPG can discover recipes and gather the metadata needed for build-time execution plan generation.

## Scope

This step changes index generation output. It does not implement BPG execution plans inside this repository.

## Tasks

1. Add recipe artifacts to the manifest or equivalent generated index.
2. Add recipe capability indexing.
3. Add node version metadata to node indexes.
4. Add runtime type metadata to node indexes.
5. Add dependency metadata for services, workers, secrets, and package artifacts.
6. Add tests for generated index contents.
7. Update documentation for index consumers.

## Index Requirements

Generated indexes should let a BPG build flow answer:

- Which recipes provide a requested capability?
- Which nodes can satisfy a recipe step's capability selector?
- Which exact node versions are available for a node ID?
- Which services and workers are required by a selected node?
- Which IO schemas must be checked before plan generation?

## Acceptance Criteria

- Recipe IDs appear in generated artifact indexes.
- Capabilities can resolve to both nodes and recipes.
- Node entries include exact node version and runtime type.
- Service node dependencies are visible from indexes.
- Existing index consumers remain compatible or have an explicit migration note.

## Notes

Resolution should still happen in BPG. This repository should provide enough indexed metadata for BPG to generate a locked plan with exact package versions, image digests, node IDs, node versions, schema versions, defaults, and workflow bindings.

