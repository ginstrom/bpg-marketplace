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

For discovery consumers, start with `generated/manifest.json`. It is the bootstrap file that declares:

* which artifact types exist
* where their source metadata lives
* which schema applies to each type
* which generated index is the primary entrypoint for querying that type

The generated indexes remain:

* `generated/index.json` for the full artifact catalog
* `generated/capabilities.json` for capability-first lookup
* `generated/templates.json` for template-only lookup
* `generated/compatibility.json` for compatibility and trust metadata

## Layout

See [docs/design.md](/home/ryan/dev/bpg-marketplace/docs/design.md) for the full design basis. The implemented repo layout follows that document:

* `registry/` source metadata for marketplace artifacts
* `schemas/` JSON Schema definitions
* `generated/` build outputs
* `examples/` workflow examples
* `scripts/` CLI entry scripts
* `src/bpg_marketplace/` shared Python logic
* `tests/` test coverage for validation and index generation
