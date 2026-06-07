# Capability Taxonomy

Machine-readable capability tags used by the marketplace registry. Recipe selectors and node packages should use these terms consistently.

See also [Composable Nodes and Recipes](composable-nodes-and-recipes.md) for how capabilities compose into recipes.

## Search and Indexing

| Capability | Description |
| --- | --- |
| `embedding` | Create vector embeddings from text |
| `tokenization` | Tokenize text for lexical search (including language-specific tokenizers such as Kuromoji) |
| `hybrid_search` | Combined lexical and vector retrieval |
| `hybrid_upsert` | Write both lexical and vector fields to a search index |
| `bm25_search` | Lexical BM25-style search preparation or query |
| `vector_search` | Vector similarity search |
| `vector_upsert` | Write vector fields to a search index |

## Audit and Compliance

| Capability | Description |
| --- | --- |
| `audit_logging` | Record auditable events to a durable ledger |
| `audit_verification` | Verify audit chain integrity |
| `compliance_reporting` | Generate compliance summaries and reports |
| `evidence_export` | Export audit evidence bundles |
| `trace_emission` | Emit distributed tracing spans for workflow steps |

## Workflow Control

| Capability | Description |
| --- | --- |
| `human_approval` | Pause workflow for human sign-off |
| `human_in_the_loop` | Interactive human participation in a workflow step |
| `workflow_pause` | Pause workflow execution |
| `workflow_resume` | Resume paused workflow execution |
| `control_flow` | Branching, looping, and conditional execution |
| `orchestration` | Coordinate multi-step workflow execution |

## Data and I/O

| Capability | Description |
| --- | --- |
| `data_io` | General structured data read/write |
| `file_io` | File system read/write operations |
| `text_processing` | Text manipulation and formatting |
| `math` | Numeric computation |

## Integration and Communication

| Capability | Description |
| --- | --- |
| `integration` | Connect to external systems |
| `http` | HTTP request/response operations |
| `email` | Send or receive email |
| `queue` | Message queue publish/consume |
| `slack` | Slack messaging and notifications |
| `notification` | General notification delivery |

## AI and Agents

| Capability | Description |
| --- | --- |
| `llm` | Large language model invocation |
| `agent` | Autonomous agent execution |

## Notes

- Capability names are concise, lowercase, and snake_case.
- Prefer a single canonical term per behavior. For example, use `tokenization` rather than language-specific aliases such as `japanese_tokenization` in recipe selectors; implementation tags on nodes convey locale specifics.
- Add new capabilities to this taxonomy when publishing node packages that introduce them.
