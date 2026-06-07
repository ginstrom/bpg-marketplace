# Step 5: Add Declarative Edge Mappings and Adapter Semantics

## Goal

Add recipe schema support for simple edge-level data adaptation so recipes can connect semantically rich node outputs to narrower node inputs without creating one-off adapter artifacts.

## Scope

This step updates recipe metadata shape and examples. It does not add runtime execution of mappings and does not introduce a new marketplace artifact type.

## Tasks

1. Extend `schemas/recipe.schema.json` so each `with` entry can be either a JSONPath string or a mapping object.
2. Support mapping objects with `from` and optional `transform` fields.
3. Add a conservative transform subset:
   - `project`: select one field from an object.
   - `map`: project one field from each object in an array.
   - `default`: provide a value when the source path is absent or null.
   - `coerce`: convert simple scalar values such as integer-to-string or string-to-number.
4. Document that these mappings compile into internal execution-plan adapter operations.
5. Document that generated internal adapters are not marketplace artifacts.
6. Document that reusable or domain-heavy transformations should be authored as normal node packages instead.
7. Update the Japanese hybrid indexing recipe from Step 4 to project Kuromoji token objects into the token string array expected by OpenSearch.
8. Add tests that validate both plain JSONPath strings and mapping objects in recipe `with` blocks.

## Mapping Shape

Use this shape for edge-level adaptation:

```json
{
  "tokens": {
    "from": "$.steps.tokenize.tokens",
    "transform": {
      "type": "map",
      "path": "$.surface"
    }
  }
}
```

The `from` value identifies recipe inputs or prior step outputs. The optional `transform` describes a simple deterministic operation over that source value.

## Adapter Boundary

Use declarative mappings for:

- field projection
- field rename
- defaulting
- flattening
- simple scalar coercion
- selecting array fields such as token surfaces

Use normal node packages for:

- language-specific normalization
- sparse-vector generation
- embedding model migration
- retrieval result shaping
- custom document construction with business rules
- expensive or reusable transformations

## Execution Plan Output

BPG should compile supported mapping objects into internal adapter operations in the locked execution plan. These internal operations should be deterministic and schema-checked, but they should not be indexed as marketplace artifacts.

## Acceptance Criteria

- Recipes can use either JSONPath strings or mapping objects in `with` blocks.
- Unsupported transform types fail recipe validation.
- Mapping objects require a non-empty `from` JSONPath.
- The Japanese hybrid indexing recipe can map Kuromoji token objects into OpenSearch token strings.
- Documentation clearly distinguishes declarative mappings, generated internal adapters, and real adapter nodes.

## Notes

Do not add a standalone `adapter` artifact type at this stage. Adapter nodes should remain ordinary `node_package` entries when they need custom runnable code.
