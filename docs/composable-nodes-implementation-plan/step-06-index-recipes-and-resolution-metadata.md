# Step 6: Index Recipes and Resolution Metadata

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
6. Add mapping metadata needed to generate internal adapter operations from recipe `with` blocks.
7. Add tests for generated index contents.
8. Add a CI check that runs index generation even though `generated/*.json` is ignored by git.
9. Update documentation for index consumers.

## Index Requirements

Generated indexes should let a BPG build flow answer:

- Which recipes provide a requested capability?
- Which nodes can satisfy a recipe step's capability selector?
- Which exact node versions are available for a node ID?
- Which services and workers are required by a selected node?
- Which IO schemas must be checked before plan generation?
- Which recipe edges require declarative mapping transforms?
- Can generated indexes be rebuilt from source metadata in CI?

## Acceptance Criteria

- Recipe IDs appear in generated artifact indexes.
- Capabilities can resolve to both nodes and recipes.
- Node entries include exact node version and runtime type.
- Service node dependencies are visible from indexes.
- Declarative mapping transforms remain visible to BPG plan generation.
- Existing index consumers remain compatible or have an explicit migration note.
- CI runs `scripts/build_index.py` so ignored generated JSON remains reproducible from checked-in registry source.

## Notes

Resolution should still happen in BPG. This repository should provide enough indexed metadata for BPG to generate a locked plan with exact package versions, image digests, node IDs, node versions, schema versions, defaults, and workflow bindings.

Keep `generated/*.json` ignored unless this repository becomes the direct distribution surface for BPG clients. CI should still build the files on every change so schema, registry, and indexer drift is caught before merge.
