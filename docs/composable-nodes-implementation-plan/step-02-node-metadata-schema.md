# Step 2: Extend Node Metadata Schema

## Goal

Extend node metadata so node packages can describe runnable code, service dependencies, worker packaging, IO contracts, and versioned nodes.

## Scope

This step changes metadata shape and validation. It should not require actual runnable node packages yet.

## Tasks

1. Extend `schemas/node.schema.json` to support runtime metadata.
2. Add node-level `version` separate from stable node `id`.
3. Add IO schema references for each node.
4. Add execution metadata for side effects, resources, network needs, secrets, and services.
5. Add package-level and node-level worker declarations.
6. Update existing registry node files to remain valid under the new schema.
7. Add tests for valid and invalid runtime declarations.

## Metadata Requirements

Node packages should support package-level fields for:

- package version
- source artifacts
- default worker image
- default worker install mode
- package-level dependencies

Individual nodes should support:

- `id`
- `version`
- `capabilities`
- `runtime.type`
- `runtime.language`
- `runtime.entrypoint`
- `runtime.task_queue`
- `runtime.image`
- `io.input_schema`
- `io.output_schema`
- `retryable`
- `idempotent`
- `side_effects`
- `execution.requires_network`
- `execution.resources`
- `execution.required_secrets`
- `execution.required_services`
- node-level worker override

Supported `runtime.type` values should include:

- `temporal_activity`
- `service_container`
- `external_service`

## Acceptance Criteria

- Existing node packages are migrated or compatibility rules are documented.
- A Temporal activity node can declare an importable entrypoint and schemas.
- A service node such as Weaviate can declare a container image without an activity entrypoint.
- A node-level worker declaration can override the package-level worker declaration.

## Notes

Model services as nodes in this step. The distinction between executable nodes and service dependency nodes should be expressed with `runtime.type`, not with a separate service artifact type.

