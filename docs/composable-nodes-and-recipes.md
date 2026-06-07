# Composable Nodes and Recipes

## Purpose

The marketplace should support real runnable code without turning the registry into an execution platform.

The core model is:

* node packages provide small, typed, executable workflow primitives
* recipes compose those primitives into higher-level capabilities
* templates package recipes into complete workflow architectures

This lets the marketplace answer both narrow and broad requests:

* "I need a Japanese tokenizer node"
* "I need OpenSearch hybrid indexing"
* "I need state of the art search for a RAG system"

## Design Principle

Prefer composable execution units over monolithic integration nodes.

For Temporal-backed systems, custom logic should run in activities. Workflow code should stay deterministic and should orchestrate activity calls, timers, retries, child workflows, and compensation. Network calls, model calls, tokenization, file IO, container operations, and search index writes belong in activities or external services.

## Artifact Layers

### Node Package

A node package is a versioned code artifact. It can contain one or more nodes.

Examples:

* `bpg-nodes-embedding`
* `bpg-nodes-tokenization`
* `bpg-nodes-opensearch`
* `bpg-nodes-weaviate`

Node packages may ship as:

* Python packages
* container images
* both, when workers can either install code locally or run a packaged worker image

The registry should describe the package and its executable nodes, but it should not contain the implementation code itself.

### Node

A node is the smallest marketplace execution primitive. In a Temporal environment, a node usually maps to one activity.

Examples:

* `embedding.create_text_embedding`
* `tokenization.kuromoji_tokenize`
* `opensearch.bm25_prepare_document`
* `opensearch.vector_upsert`
* `opensearch.hybrid_query`
* `rerank.cross_encoder`

Each node should declare:

* stable node id
* concrete node version
* capability tags
* runtime type
* activity entrypoint
* input schema
* output schema
* side effects
* retry and idempotency properties
* required secrets
* required services
* resource needs
* observability support

### Recipe

A recipe is a machine-readable composition of smaller nodes into a useful capability.

Recipes are not arbitrary prose examples. They are structured plans that an agent, workflow generator, or developer can translate into Temporal workflow code.

Examples:

* `opensearch.hybrid_index_japanese_chunk`
* `rag.state_of_the_art_search`
* `retrieval.hybrid_then_rerank`
* `retrieval.multi_index_fallback`

A recipe should describe:

* required capabilities
* ordered or graph-shaped steps
* data flow between steps
* required node ids or capability selectors
* retry boundaries
* failure handling
* recommended defaults
* tunable parameters
* expected quality and latency tradeoffs

Recipes should compose nodes by capability where possible and by explicit node id where necessary.

### Template

A template is a complete workflow architecture or reference implementation.

Templates can include one or more recipes plus surrounding operational behavior:

* ingestion
* approval
* observability
* deployment
* access control
* evaluation
* rollback or reindexing

For example, an enterprise RAG template might use a search recipe, an approval policy, an ingestion recipe, and observability nodes.

## Proposed Runtime Model

### Atomic Node Execution

For Temporal-backed BPG systems, each runnable node should have a Temporal activity adapter.

Example node metadata:

```json
{
  "id": "tokenization.kuromoji_tokenize",
  "capabilities": ["tokenization"],
  "runtime": {
    "type": "temporal_activity",
    "language": "python",
    "entrypoint": "bpg_nodes_tokenization.activities:kuromoji_tokenize",
    "task_queue": "search"
  },
  "io": {
    "input_schema": "schemas/kuromoji_tokenize.input.json",
    "output_schema": "schemas/kuromoji_tokenize.output.json"
  },
  "retryable": true,
  "idempotent": true,
  "side_effects": [],
  "execution": {
    "requires_network": false,
    "resources": {
      "cpu": "250m",
      "memory": "512Mi"
    }
  }
}
```

The activity entrypoint is worker-facing. The workflow-facing interface is the input/output schema.

### Node Identity and Versioning

Recipes may select nodes either by capability or by exact node id. Exact node ids are useful for critical steps where the recipe depends on a specific behavior, such as `tokenization.kuromoji_tokenize` for Japanese BM25 preparation.

Node ids should be stable logical identifiers. Versions should be separate from ids.

Recommended reference forms:

```json
{
  "select": {
    "node": "tokenization.kuromoji_tokenize",
    "version": ">=1.2,<2.0"
  }
}
```

and:

```json
{
  "select": {
    "capability": "tokenization",
    "preferred_node": "tokenization.kuromoji_tokenize",
    "version": ">=1.2,<2.0"
  }
}
```

`preferred_node` is a string node id with an optional sibling `version` constraint on `select`. This mirrors the `select.node` + `select.version` pattern and keeps the recipe schema flat. The registry and resolution index use this form consistently.

The marketplace registry can expose available versions, but BPG should resolve them during its build flow into a locked execution plan. That plan should record exact package versions, container digests, node ids, node versions, schema versions, and selected defaults.

Breaking changes to node input/output contracts should require a major version change. Non-breaking additions can be minor versions if old recipe mappings remain valid.

Node package metadata should publish concrete node versions. Recipe metadata should use version constraints. Generated execution plans should pin exact resolved versions.

Supported version constraint grammar:

- Single clause: `>=1.0`, `<=2.0`, `>1.0`, `<2.0`, `==1.0`, or `=1.0`
- Compound ranges: comma-separated AND clauses, for example `>=1.2,<2.0`
- Whitespace around commas and operators is tolerated
- Pre-release suffixes on versions (for example `1.2.0-beta`) compare on the numeric prefix

### Service Nodes

Some marketplace entries represent service dependencies rather than custom workflow code.

Example:

```json
{
  "id": "weaviate.service",
  "capabilities": ["vector_database"],
  "runtime": {
    "type": "service_container",
    "image": "semitechnologies/weaviate:latest"
  }
}
```

Service nodes can be dependencies of executable nodes or recipes.

Modeling services as nodes is preferable to introducing a separate artifact type at this stage. A service such as Weaviate or OpenSearch is still a marketplace-resolvable operational primitive with capabilities, versions, trust metadata, dependencies, and observability expectations. The distinction should live in `runtime.type`, for example `temporal_activity`, `service_container`, or `external_service`.

Use `service_container` for dependencies you deploy and operate (for example OpenSearch). Use `external_service` for hosted APIs you connect to but do not run (for example `embedding.openai_api` for the OpenAI embeddings endpoint). See the registry example in `registry/nodes/bpg-nodes-search.json`.

The tradeoff is that the term "node" becomes broader than "callable workflow step." That is acceptable if every recipe step declares whether it invokes an executable node or depends on a service node. This keeps dependency resolution unified while avoiding a separate service registry too early.

### Worker Packaging

The marketplace should support two install modes:

* package install: install Python node packages into an existing worker
* worker image: run a prebuilt worker image containing the node package and runtime dependencies

Package install is flexible during development. Worker images are more predictable in production, especially for dependencies such as Kuromoji bindings, JVM-backed tokenizers, GPU libraries, or native search clients.

Worker images may be declared at either package or node level.

Package-level worker images are the default for packages whose nodes share a runtime environment. Node-level worker images are useful when one package contains nodes with meaningfully different runtime needs, such as a lightweight text activity and a GPU reranking activity.

## Recipe Example: Japanese Hybrid Indexing

Goal:

Convert an incoming chunk into searchable OpenSearch fields for hybrid retrieval.

Recipe:

```json
{
  "id": "bpg.recipes.opensearch_hybrid_index_japanese_chunk",
  "name": "OpenSearch Hybrid Index Japanese Chunk",
  "type": "recipe",
  "summary": "Embeds a text chunk, tokenizes it for Japanese BM25 search, and writes both lexical and vector fields to OpenSearch.",
  "capabilities": [
    "hybrid_search",
    "hybrid_upsert",
    "embedding",
    "tokenization"
  ],
  "inputs": {
    "chunk": {
      "type": "object",
      "required": ["id", "text"],
      "properties": {
        "id": { "type": "string" },
        "text": { "type": "string" },
        "metadata": { "type": "object" }
      }
    },
    "index": { "type": "string" },
    "embedding_model": { "type": "string" }
  },
  "steps": [
    {
      "id": "embed",
      "select": {
        "capability": "embedding",
        "preferred_node": "embedding.create_text_embedding",
        "version": ">=0.1.0,<1.0.0"
      },
      "with": {
        "text": "$.chunk.text",
        "model": "$.embedding_model"
      }
    },
    {
      "id": "tokenize",
      "select": {
        "capability": "tokenization",
        "preferred_node": "tokenization.kuromoji_tokenize",
        "version": ">=0.1.0,<1.0.0"
      },
      "with": {
        "text": "$.chunk.text",
        "mode": "search"
      }
    },
    {
      "id": "upsert",
      "select": {
        "capability": "hybrid_upsert",
        "preferred_node": "opensearch.hybrid_upsert",
        "version": ">=0.1.0,<1.0.0"
      },
      "with": {
        "index": "$.index",
        "id": "$.chunk.id",
        "text": "$.chunk.text",
        "tokens": {
          "from": "$.steps.tokenize.token_details",
          "transform": {
            "type": "map",
            "path": "$.surface"
          }
        },
        "vector": "$.steps.embed.vector",
        "metadata": "$.chunk.metadata"
      }
    }
  ],
  "failure_policy": {
    "retry_steps": ["embed", "tokenize", "upsert"],
    "compensation": []
  }
}
```

This recipe is intentionally smaller than a full RAG template. It only describes indexing one chunk.

## Recipe Example: State of the Art RAG Search

Goal:

Provide a high-quality retrieval plan for RAG systems while letting implementations swap providers.

Recipe:

```json
{
  "id": "bpg.recipes.rag_state_of_the_art_search",
  "name": "State of the Art RAG Search",
  "type": "recipe",
  "summary": "Runs hybrid retrieval, optional query rewriting, metadata filtering, reranking, and citation-ready result shaping.",
  "capabilities": [
    "query_rewriting",
    "hybrid_search",
    "metadata_filtering",
    "reranking",
    "retrieval_result_shaping"
  ],
  "steps": [
    {
      "id": "rewrite_query",
      "optional": true,
      "select": {
        "capability": "query_rewriting"
      }
    },
    {
      "id": "hybrid_retrieve",
      "select": {
        "capability": "hybrid_search"
      }
    },
    {
      "id": "rerank",
      "select": {
        "capability": "reranking"
      }
    },
    {
      "id": "shape_results",
      "select": {
        "capability": "retrieval_result_shaping"
      }
    }
  ],
  "defaults": {
    "top_k_retrieve": 50,
    "top_k_rerank": 8,
    "include_citations": true
  },
  "tradeoffs": {
    "quality": "high",
    "latency": "medium",
    "cost": "medium"
  }
}
```

This recipe should not force OpenSearch, Weaviate, a specific embedding model, or a specific reranker. It should define the capability graph and recommended defaults. Marketplace resolution can then choose compatible nodes based on trust level, environment, language support, cost, and installed packages.

## Composition Semantics

Recipes should support both linear and graph-shaped flows.

Minimum useful semantics:

* `steps`: named executable units
* `select.capability`: choose any compatible node
* `select.node`: require a specific node id
* `select.preferred_node`: use a specific node when available
* `select.version`: constrain node versions
* `with`: map recipe inputs and prior step outputs to node inputs using a standard mapping format
* `optional`: allow a step to be skipped when no compatible node is available
* `defaults`: recommended parameters
* `failure_policy`: retry, fallback, and compensation behavior

Data mapping should use a standard format. JSONPath is the preferred default because recipe inputs, step outputs, and generated execution plans are JSON-shaped, and JSONPath is widely recognizable to both humans and tooling. BPG should define the supported JSONPath subset rather than accepting every dialect-specific extension.

### Declarative Edge Mappings and Adapters

Recipes should treat data adaptation as an edge concern before introducing new executable nodes.

For example, a Kuromoji tokenizer may return rich token objects, while an OpenSearch BM25 field may only need token strings. The recipe should be able to declare that projection at the edge between steps:

```json
{
  "id": "upsert",
  "select": {
    "node": "opensearch.hybrid_upsert",
    "version": ">=0.1.0"
  },
  "with": {
    "tokens": {
      "from": "$.steps.tokenize.token_details",
      "transform": {
        "type": "map",
        "path": "$.surface"
      }
    }
  }
}
```

BPG should compile simple declarative mappings into the locked execution plan. The generated plan may contain internal adapter operations, but the marketplace should not require a separate adapter artifact for every field projection.

**Implemented today:** The marketplace validates declarative mappings and records them in `generated/resolution.json`. BPG compilation of transforms into internal adapter operations is planned in the BPG repository.

Use declarative mappings for:

* field projection
* field rename
* defaulting
* flattening
* simple scalar coercion
* selecting array fields such as token surfaces

Use real adapter nodes when the transformation is reusable, version-sensitive, domain-specific, expensive, or policy-bearing. Examples include language-specific normalization, sparse-vector generation, model-specific embedding migration, retrieval result shaping, and custom document construction with nontrivial business rules.

This keeps recipes composable without causing the marketplace to fill with one-off adapter packages. Adapter nodes remain normal nodes with `runtime.type: temporal_activity`; internal execution-plan adapters are generated from declarative mappings and are not marketplace artifacts.

Later semantics can include:

* parallel branches
* conditionals
* fan-out and fan-in
* quality gates
* evaluation hooks
* cost and latency budgets

The first implementation should avoid a full workflow language. Recipes should be structured enough for build-time plan generation, code generation, and discovery, but not so expressive that the marketplace becomes a workflow engine.

## Build-Time Execution Plans

**Implemented today:** The marketplace generates `generated/resolution.json` with node resolution metadata, recipe step mappings, and capability indexes. Locked execution plan generation from that metadata is planned in the BPG repository.

BPG should generate execution plans as part of its terraform-like build flow.

The marketplace recipe is the authored, reusable intent:

* capability graph
* node preferences
* version constraints
* mapping rules
* operational defaults

The BPG build output is the deployable plan:

* exact node ids
* exact node versions
* package versions
* container image digests
* worker assignment
* task queues
* resolved services
* validated input/output schema links
* selected defaults
* generated declarative mapping adapters
* generated workflow/activity bindings

This keeps runtime behavior predictable. Runtime systems should execute the locked plan rather than re-resolving marketplace choices dynamically on every workflow run.

## Capability Resolution

Capability tags should match the vocabulary in [Capability Taxonomy](capability-taxonomy.md).

When a recipe selects by capability, the marketplace consumer should resolve candidates using:

1. BPG compatibility
2. required runtime type
3. required language or worker environment
4. required secrets and services
5. trust level
6. input/output schema compatibility
7. implementation tags, such as `japanese`, `kuromoji`, `opensearch`, or `gpu`
8. operational preferences, such as cost, latency, or blessed packages

Resolution should produce an explicit lock file or generated workflow plan. That plan should record the exact node package versions, image digests, node ids, and selected defaults.

Exact node references are resolved the same way as capability references, except candidate selection starts from the named node id and then checks version, runtime, schema, worker, service, and secret compatibility.

Capability references remain important for recipes such as state of the art RAG search, where the best implementation may vary by deployment. Exact references are appropriate for behavior-sensitive steps where the recipe author wants a known implementation.

## Trust and Safety

Adding runnable code increases marketplace risk.

Trust metadata should eventually account for:

* schema-valid metadata
* package installability
* importability of declared entrypoints
* container image availability
* pinned image digests
* signed artifacts
* SBOM availability
* vulnerability scan status
* deterministic workflow separation
* declared side effects matching implementation review
* tests for input/output schemas

Community packages can be discoverable with minimal checks. Verified and blessed packages should require stronger checks.

Schema compatibility should be enforced by BPG during build-time plan generation. The marketplace should still provide lightweight authoring checks so contributors can verify node packages before publishing.

Useful lightweight checks:

* validate registry metadata against JSON Schema
* verify package or image references are reachable
* import declared Python activity entrypoints when package dependencies are installed
* load declared input/output schemas
* verify recipe mappings reference valid inputs and prior step ids
* verify declarative mapping transforms are in the supported subset
* check that exact node references and version constraints can resolve against the local registry

These checks should be available both in marketplace CI and from BPG, for example as a `bpg marketplace verify` or equivalent build-time command.

## Observability

Nodes and recipes should declare observability support separately.

Node-level observability:

* activity spans
* metrics
* structured logs
* error classification

Recipe-level observability:

* step timing
* selected implementation ids
* retrieval quality counters
* token counts
* embedding model ids
* index names
* reranking counts

For RAG search recipes, observability should make it possible to answer:

* which search path was used
* which retriever produced each result
* which reranker changed ordering
* how many candidates were discarded
* what latency each step added

## Recommended Artifact Model

The current `template` artifact should remain for complete workflow examples.

Add a distinct `recipe` artifact type for composable capability plans.

Recommended marketplace types:

* `node_package`: installable code package containing nodes
* `recipe`: structured composition of nodes or capabilities
* `template`: complete workflow architecture or reference implementation
* `pack`: bundle of packages, recipes, templates, and policies
* `policy`: governance and operational rules

Recipes should be allowed in packs and templates. Templates should be allowed to reference recipes directly.

## Implementation Status

The marketplace foundation described in this document is implemented. See the [Composable Nodes Implementation Plan](composable-nodes-implementation-plan/index.md) for step-by-step delivery history and [Follow-Up Work](composable-nodes-implementation-plan/follow-up-work.md) for remaining polish.

Remaining BPG-side work (out of scope for this repository):

- locked execution plan generation from `generated/resolution.json`
- compilation of declarative mapping transforms into internal adapter operations
- generated workflow/activity bindings
- worker image digest pinning at build time
