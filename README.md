# bpg-marketplace

`bpg-marketplace` is a GitHub-native registry for reusable BPG workflow components, templates, packs, and policies.

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

## Layout

See [docs/design.md](/home/ryan/dev/bpg-marketplace/docs/design.md) for the full design basis. The implemented repo layout follows that document:

* `registry/` source metadata for marketplace artifacts
* `schemas/` JSON Schema definitions
* `generated/` build outputs
* `examples/` workflow examples
* `scripts/` CLI entry scripts
* `src/bpg_marketplace/` shared Python logic
* `tests/` test coverage for validation and index generation
