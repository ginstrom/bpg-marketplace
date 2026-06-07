# Step 4: Add Japanese Hybrid Indexing Recipe

## Goal

Add a concrete recipe that composes embedding, Japanese tokenization, and OpenSearch upsert nodes for hybrid indexing.

## Scope

This step adds a recipe artifact and tests that it validates. It should use the recipe schema from Step 1 and the sample nodes from Step 3.

## Tasks

1. Add `registry/recipes/opensearch-hybrid-index-japanese-chunk.json`.
2. Define recipe-level inputs for `chunk`, `index`, and `embedding_model`.
3. Define recipe-level outputs for the upsert result.
4. Add steps for `embed`, `tokenize`, and `upsert`.
5. Use JSONPath mappings in each step's `with` block.
6. Use an exact or preferred reference to `tokenization.kuromoji_tokenize`.
7. Use an exact or preferred reference to `opensearch.hybrid_upsert`.
8. Use a declarative edge mapping to project Kuromoji token objects into the OpenSearch token string array.
9. Add tests that validate the recipe.

## Required Step Graph

The recipe should run:

1. `embed`: converts `$.chunk.text` to `$.steps.embed.vector`.
2. `tokenize`: converts `$.chunk.text` to `$.steps.tokenize.tokens` and `$.steps.tokenize.token_details`.
3. `upsert`: writes `$.chunk.text`, `$.steps.embed.vector`, and projected token surfaces from `$.steps.tokenize.token_details` to OpenSearch.

## Acceptance Criteria

- The recipe validates against `schemas/recipe.schema.json`.
- Every exact node reference can resolve to a registry node.
- Every version constraint can resolve to at least one node version.
- Every JSONPath reference points to a declared recipe input or prior step output.
- The token mapping documents the Kuromoji-to-OpenSearch adaptation instead of requiring a separate adapter node.

## Notes

This recipe should remain smaller than a full RAG template. It describes indexing one chunk, not ingestion, evaluation, or retrieval.

If Step 5 has not landed yet, this recipe may temporarily use plain JSONPath strings. Once declarative edge mappings are available, the upsert step should use a mapping object such as:

```json
{
  "tokens": {
    "from": "$.steps.tokenize.token_details",
    "transform": {
      "type": "map",
      "path": "$.surface"
    }
  }
}
```
