# Contributing

## Principles

* add new marketplace artifacts under `registry/`
* validate metadata against the matching schema in `schemas/`
* update or regenerate discovery outputs in `generated/`
* add or extend tests when changing validation or indexing behavior

## Local Workflow

Run the full check sequence after registry or Python changes:

```bash
python3 -m unittest discover -s tests
python3 scripts/validate_registry.py
python3 scripts/verify_registry.py --mode static
python3 scripts/build_index.py
```

### When to run each check

| Check | When |
| --- | --- |
| Unit tests | After any Python change to validation, indexing, or verification |
| `validate_registry.py` | After any registry or schema change |
| `verify_registry.py --mode static` | After node metadata, image, or entrypoint reference changes |
| `build_index.py` | After registry changes that affect discovery or resolution output |
| `verify_registry.py --mode runtime-light` | After installing the node package locally (see [Temporal Activity Adapters](temporal-activity-adapters.md#verification-modes)) |

CI runs the same checks (using `python` after `setup-python`) plus `verify_packages.py` and an index reproducibility check:

```bash
python3 scripts/check_index_reproducibility.py
```

See [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

## Node package authors

If you are adding `temporal_activity` nodes, read [Temporal Activity Adapter Expectations](temporal-activity-adapters.md) for entrypoint, worker, and service dependency conventions.

For a minimal authoring reference, see [`examples/node-authoring/sample-greet-node/`](../examples/node-authoring/sample-greet-node/).

## Broader context

* [BPG](https://github.com/ginstrom/bpg) — workflow platform that consumes marketplace metadata at build time
* [Composable Nodes Implementation Plan](composable-nodes-implementation-plan/index.md) — delivery history for the composable nodes foundation
* [Follow-Up Work](composable-nodes-implementation-plan/follow-up-work.md) — tracked polish and deferred items from the implementation audit
