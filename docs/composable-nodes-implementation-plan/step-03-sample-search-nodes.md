# Step 3: Add Sample Atomic Search Nodes

## Goal

Add realistic sample node metadata for the atomic building blocks used by hybrid search recipes.

## Scope

This step adds registry examples and IO schema files. It does not require the actual Python packages or containers to exist unless the lightweight verification step has already been implemented.

## Tasks

1. Add an embedding activity node.
2. Add a Kuromoji Japanese tokenization activity node.
3. Add an OpenSearch hybrid upsert activity node.
4. Add an OpenSearch service node.
5. Add a Weaviate service node if not already represented with service runtime metadata.
6. Add input and output schema files for each executable node.
7. Add tests that validate the sample nodes against the node schema.

## Suggested Nodes

- `embedding.create_text_embedding`
- `tokenization.kuromoji_tokenize`
- `opensearch.hybrid_upsert`
- `opensearch.service`
- `weaviate.service`

## Required Contracts

The embedding node should accept:

- text
- model
- optional dimensions

The embedding node should return:

- vector
- model
- dimensions

The Kuromoji node should accept:

- text
- optional mode

The Kuromoji node should return:

- tokens
- normalized_text

The OpenSearch upsert node should accept:

- index
- id
- text
- tokens
- vector
- metadata

The OpenSearch upsert node should return:

- index
- id
- result

## Acceptance Criteria

- All sample nodes validate against `schemas/node.schema.json`.
- All referenced IO schemas exist and validate as JSON Schema documents.
- Service nodes use `runtime.type: service_container`.
- Executable nodes use `runtime.type: temporal_activity`.

## Notes

Use stable logical node IDs and explicit node versions. Avoid provider-specific assumptions in the embedding node unless they are reflected in capabilities or implementation tags.

