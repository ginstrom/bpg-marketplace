# Step 9: Document Temporal Activity Adapter Expectations

## Goal

Document how node package authors should expose Temporal-compatible activity code for marketplace nodes.

## Scope

This step is documentation-focused. It should produce clear author guidance and examples, not runtime enforcement.

## Tasks

1. Add documentation for Temporal workflow and activity separation.
2. Define expectations for activity entrypoints.
3. Define how activity inputs and outputs map to JSON Schemas.
4. Define retry, idempotency, and side-effect declarations.
5. Define worker package and worker image expectations.
6. Define service dependency declarations.
7. Add a small example activity adapter.
8. Link the guidance from the implementation plan and main docs index.

## Required Guidance

The documentation should state:

- Workflow code must stay deterministic.
- Network calls, model calls, tokenization, file IO, container operations, and search writes belong in activities or external services.
- Activity functions should accept schema-shaped inputs and return schema-shaped outputs.
- Node metadata is the contract between recipes, BPG build-time planning, and worker code.
- Service nodes such as OpenSearch and Weaviate are dependencies, not activity entrypoints.

## Acceptance Criteria

- A node author can understand how to declare a Temporal activity node.
- A node author can understand when to use a service node.
- A BPG engineer can understand how generated execution plans should bind recipe steps to activity calls.
- The documentation is linked from `docs/index.md`.

## Notes

Keep examples small. The purpose is to establish expectations for package authors before stronger verification and generated worker bindings are implemented.
