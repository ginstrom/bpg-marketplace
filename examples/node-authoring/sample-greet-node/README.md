# Sample Greet Node

Minimal Temporal activity adapter used in marketplace documentation.

This example is intentionally small. It shows the expected split between:

- implementation code in the Python package
- thin activity exports for worker registration
- marketplace registry metadata and JSON Schemas

## Files

```text
sample-greet-node/
  greet_node/
    __init__.py
    activities.py
  registry-snippet.json
  schemas/
    example.greet.input.schema.json
    example.greet.output.schema.json
```

## Python package

Implementation (`greet_node/__init__.py`) owns business logic and SDK metadata.
Activity adapter (`greet_node/activities.py`) re-exports the callable expected by registry `runtime.entrypoint`.

## Registry metadata

`registry-snippet.json` shows the node definition you would add to `registry/nodes/<package>.json` in this repository.

## Related documentation

- [Temporal Activity Adapter Expectations](../../../docs/temporal-activity-adapters.md)
