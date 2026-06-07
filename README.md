# bpg-marketplace

`bpg-marketplace` is a GitHub-native registry for reusable [BPG](https://github.com/ginstrom/bpg) workflow components, recipes, templates, packs, and policies.

This repository is structured around machine-readable metadata rather than a visual application. The current scaffold includes:

* typed JSON Schemas for each artifact class
* sample registry artifacts
* index-building and validation scripts
* example workflow placeholders
* CI and test coverage

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m unittest discover -s tests
python3 scripts/build_index.py
python3 scripts/validate_registry.py
```

For discovery consumers, start with `generated/manifest.json`. It is the bootstrap file that declares:

* which artifact types exist
* where their source metadata lives
* which schema applies to each type
* which generated index is the primary entrypoint for querying that type

The generated indexes remain:

* `generated/index.json` for the full artifact catalog
* `generated/capabilities.json` for artifact-level capability-first lookup
* `generated/resolution.json` for [BPG](https://github.com/ginstrom/bpg) build-time recipe and node resolution metadata
* `generated/recipes.json` for recipe-only lookup
* `generated/templates.json` for template-only lookup
* `generated/compatibility.json` for compatibility and trust metadata

Use `generated/resolution.json` when generating locked execution plans. It includes node-level capability candidates, exact node versions, runtime and worker metadata, service and secret dependencies, IO schema references, recipe step selectors, and declarative mapping transforms. The older `generated/capabilities.json` remains artifact-level for existing discovery consumers.

## Documentation

See [docs/index.md](docs/index.md) for the full documentation index. Key entry points:

* [Design](docs/design.md) — marketplace goals, artifact model, and trust levels
* [Composable Nodes and Recipes](docs/composable-nodes-and-recipes.md) — node packages, recipes, and build-time execution plans
* [Contributing](docs/contributing.md) — local validation workflow and authoring guidance

The marketplace provides discovery metadata and validation for components consumed by the [BPG](https://github.com/ginstrom/bpg) build flow. Runtime execution, workflow orchestration, and CLI tooling live in the [BPG repository](https://github.com/ginstrom/bpg).

## Layout

See [docs/design.md](docs/design.md) for the full design basis. The implemented repo layout follows that document:

* `registry/` source metadata for marketplace artifacts
* `schemas/` JSON Schema definitions
* `generated/` build outputs
* `examples/` workflow examples
* `scripts/` CLI entry scripts
* `src/bpg_marketplace/` shared Python logic
* `tests/` test coverage for validation and index generation
