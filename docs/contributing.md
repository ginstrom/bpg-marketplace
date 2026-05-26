# Contributing

## Principles

* add new marketplace artifacts under `registry/`
* validate metadata against the matching schema in `schemas/`
* update or regenerate discovery outputs in `generated/`
* add or extend tests when changing validation or indexing behavior

## Local Workflow

```bash
python3 -m unittest discover -s tests
python3 scripts/validate_registry.py
python3 scripts/build_index.py
```
