# Follow-Up 6: Add an `external_service` Registry Example

[Documentation](../index.md) › [Implementation Plan](index.md) › [Follow-Up Work](follow-up-work.md) › Follow-Up 6: `external_service` Registry Example

**Status:** [x] Complete

## Goal

Publish a minimal registry node that demonstrates `runtime.type: external_service` so authors have a concrete reference alongside `temporal_activity` and `service_container` examples.

## Scope

Registry metadata, IO schemas, documentation, and validation tests. No runnable integration with the external service itself.

## Background

`schemas/node.schema.json` and `src/bpg_marketplace/validation.py` accept `external_service` as a runtime type, but no checked-in node package demonstrates it. `docs/temporal-activity-adapters.md` mentions the type in passing.

## Prerequisites

- [ ] Identify a real external dependency worth publishing (for example a managed embedding API, hosted search endpoint, or third-party compliance API).
- [ ] Confirm the dependency has a stable connection contract (base URL, auth model, required headers).

## Tasks

- [ ] Add or extend a node package JSON under `registry/nodes/` with one `external_service` node.
- [ ] Define minimal IO schemas under `schemas/` for the service's connection or invocation contract.
- [ ] Declare capabilities appropriate to the service (for example `embedding` for a hosted embedding API).
- [ ] Document required secrets or environment variables in node metadata.
- [ ] Add the node as a `required_services` dependency on at least one activity node or reference it in a recipe comment/doc example.
- [ ] Run `python3 scripts/validate_registry.py` and `python3 scripts/verify_registry.py --mode static`.
- [ ] Add a short section to `docs/temporal-activity-adapters.md` or `docs/composable-nodes-and-recipes.md` contrasting `external_service` with `service_container`.
- [ ] Rebuild index with `python3 scripts/build_index.py` and confirm the node appears in `generated/resolution.json`.

## Example Shape

```json
{
  "id": "example.external_api",
  "capabilities": ["example_capability"],
  "runtime": {
    "type": "external_service",
    "provider": "example",
    "endpoint_env": "EXAMPLE_API_URL"
  },
  "io": {
    "input_schema": "schemas/example_external.input.schema.json",
    "output_schema": "schemas/example_external.output.schema.json"
  }
}
```

Adjust fields to match the actual `node.schema.json` requirements for `external_service` nodes.

## Acceptance Criteria

- At least one checked-in node uses `runtime.type: external_service`.
- Registry validation and static verification pass.
- Documentation explains when to use `external_service` versus `service_container`.
- The example uses a real or realistic dependency name, not a placeholder that will be deleted immediately.

## Notes

**Defer this step** until a concrete external dependency is ready to publish. A fabricated placeholder node adds maintenance burden without author value.

If no dependency is available soon, mark this step blocked and document the intended shape in `docs/composable-nodes-and-recipes.md` only.

## References

- [Node schema](../../schemas/node.schema.json)
- [Validation logic](../../src/bpg_marketplace/validation.py)
- [Temporal Activity Adapter Expectations](../temporal-activity-adapters.md)
- [OpenSearch service example](../../registry/nodes/opensearch.json) — `service_container` contrast
