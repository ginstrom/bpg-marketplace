# Temporal Activity Adapter Expectations

Author guidance for exposing Temporal-compatible activity code in BPG node packages.

## Purpose

The marketplace registry describes runnable nodes. Node package repositories provide the implementation. This document explains how those two sides connect so that:

- node authors know how to structure Python packages and registry metadata
- recipe authors know which nodes are callable workflow steps
- BPG engineers know how build-time execution plans bind recipe steps to worker activity calls

For the broader composable-nodes model, see [Composable Nodes and Recipes](composable-nodes-and-recipes.md).

## Workflow and activity separation

Temporal workflows must stay deterministic. Workflow code orchestrates activity calls, timers, retries, child workflows, and compensation. It should not perform nondeterministic or external work directly.

Put these operations in activities or external services, not in workflow code:

- network calls
- model inference
- tokenization
- file IO
- container operations
- search index writes

In BPG terms:

| Layer | Responsibility |
| --- | --- |
| Workflow | Graph execution, retries, approvals, compensation, observability hooks |
| Activity | One node's business logic, called with a schema-shaped payload |
| Service node | Long-running dependency such as OpenSearch, Weaviate, or Postgres audit storage |

Service nodes such as `opensearch.service` and `weaviate.service` are dependencies. They are not activity entrypoints and should not appear as executable recipe steps.

## Node metadata is the contract

Node metadata is the contract between recipes, BPG build-time planning, and worker code.

Recipes reference nodes by id or capability. BPG resolves those references into a locked execution plan with exact package versions, entrypoints, task queues, schemas, and service dependencies. Workers execute the locked plan at runtime.

The activity entrypoint is worker-facing. The workflow-facing interface is the input and output JSON Schema.

## Package layout

A typical Python node package contains:

```text
bpg-nodes-example/
  pyproject.toml
  src/
    bpg_nodes_example/
      __init__.py      # node implementations and @node metadata
      activities.py    # thin Temporal entrypoint exports
```

Recommended conventions:

- implement node logic once in `__init__.py` (or dedicated modules)
- expose importable callables from `activities.py` for worker registration
- declare one marketplace registry file per package under `registry/nodes/`
- store IO schemas under `schemas/nodes/` and `schemas/services/`

Real packages in the BPG repository follow this pattern:

- `bpg-nodes-search` for embedding and tokenization activities
- `bpg-nodes-audit` for optional audit helper activities

## Activity entrypoint expectations

Executable nodes use `runtime.type: temporal_activity`.

Registry metadata must declare:

- `runtime.language` — today this is `python`
- `runtime.entrypoint` — dotted import path to a callable
- `runtime.task_queue` — worker queue that hosts the activity
- `runtime.image` — optional but recommended worker image for production

Entrypoint format:

```text
<module>.<attribute>
```

Examples from the registry:

- `bpg_nodes_search.activities.create_text_embedding`
- `bpg_nodes_audit.activities.export_audit_bundle`

Marketplace runtime-light verification imports the module path and checks that the final attribute exists. Use a real function or callable object, not a string alias.

### Thin `activities.py` adapter

Keep Temporal entrypoints thin. Re-export the implementation callable so workers can register a stable module path:

```python
"""Temporal activity entrypoints."""

from bpg_nodes_example import greet

__all__ = ["greet"]
```

### Implementation with `@node`

Use the BPG SDK `@node` decorator to attach framework metadata to the implementation:

```python
from typing import Any

from bpg_sdk import node
from bpg_sdk.manifest import Idempotency, RetrySafety, SideEffects

_PKG = "bpg.nodes.example@v1"


@node(
    package=_PKG,
    node_id="example.greet",
    input_schema={
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "greeted": {"type": "boolean"},
        },
        "required": ["message", "greeted"],
    },
    capabilities=["example"],
    side_effects=SideEffects.NONE,
    idempotency=Idempotency.IDEMPOTENT,
    retry_safety=RetrySafety.SAFE,
)
def greet(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name", "")).strip()
    if not name:
        raise ValueError("example.greet requires name")
    return {"message": f"Hello, {name}", "greeted": True}
```

Activity functions should:

- accept one `dict[str, Any]` payload shaped like the input schema
- return one `dict[str, Any]` shaped like the output schema
- raise explicit validation errors for missing required fields
- avoid hidden global state that breaks retries

See the full minimal example in [examples/node-authoring/sample-greet-node](../examples/node-authoring/sample-greet-node/README.md).

## Mapping activities to JSON Schemas

Each node declares IO contracts in registry metadata:

```json
"io": {
  "input_schema": "schemas/nodes/example.greet.input.schema.json",
  "output_schema": "schemas/nodes/example.greet.output.schema.json"
}
```

Authoring rules:

1. Keep marketplace JSON Schema files as the published contract.
2. Keep `@node` `input_schema` and `output_schema` aligned with those files.
3. Treat recipe `with` mappings and process-spec node `config` as partial input objects validated against the input schema.
4. Treat activity return values as full output objects validated against the output schema.
5. Use `additionalProperties: false` unless the node intentionally accepts extension fields.

Recipe steps pass inputs with JSONPath references such as `$inputs.run_id` or `$.steps.export.bundle`. BPG validates those mappings during build and may generate internal adapter steps for simple field projection.

## Retry, idempotency, and side effects

Declare operational semantics in both the Python package and registry metadata.

### Python package (`bpg_sdk.manifest`)

| Field | Values | Meaning |
| --- | --- | --- |
| `side_effects` | `none`, `reads`, `writes`, `external` | Whether the activity mutates state or reaches outside the worker |
| `idempotency` | `idempotent`, `non_idempotent`, `conditional` | Whether repeated execution with the same input is safe |
| `retry_safety` | `safe`, `unsafe`, `conditional` | Whether Temporal retries are generally safe |

### Registry node metadata

| Field | Type | Meaning |
| --- | --- | --- |
| `retryable` | boolean | Whether Temporal should retry transient failures |
| `idempotent` | boolean | Whether callers can safely repeat the same request |
| `side_effects` | string array | Operational tags used by planners and reviewers |

Common registry `side_effects` tags:

- `fs_read`, `fs_write`
- `network_io`
- `data_write`

Choose conservative values. If an activity sends email, opens a ticket, or writes to an index, declare the side effect even when the implementation is best-effort.

Examples:

| Node behavior | `retryable` | `idempotent` | `side_effects` |
| --- | --- | --- | --- |
| Pure transform / embed text | `true` | `true` | `[]` |
| Read audit ledger | `true` | `true` | `fs_read` |
| Upsert to OpenSearch | `true` | `true` | `network_io`, `data_write` |
| Send Slack notification | `false` | `false` | `network_io` |

## Worker package and worker image expectations

Node packages may ship in two install modes:

| Mode | Registry field | When to use |
| --- | --- | --- |
| Package install | `worker.install_mode: package` | Development and shared worker pools that install Python deps at startup |
| Worker image | `worker.install_mode: container` | Production images with native deps, GPU libraries, or pinned environments |

Declare worker metadata at package level:

```json
"worker": {
  "image": "ghcr.io/ginstrom/bpg-nodes-search-worker:0.1.0",
  "install_mode": "package",
  "task_queue": "bpg-search"
}
```

Override at node level when one package contains heterogeneous runtimes, for example a lightweight tokenizer activity and a GPU reranker activity.

Production guidance:

- pin worker images by digest in generated execution plans
- keep package version, node version, and worker image tag aligned
- declare `runtime.task_queue` consistently with `worker.task_queue` unless a node intentionally targets a dedicated queue

## Service dependency declarations

Service dependencies are marketplace nodes with `runtime.type: service_container` or `runtime.type: external_service`.

Executable nodes declare dependencies in `execution.required_services`:

```json
"execution": {
  "required_services": ["opensearch.service"],
  "required_secrets": ["OPENSEARCH_USERNAME", "OPENSEARCH_PASSWORD"],
  "requires_network": true,
  "resources": {
    "cpu": "500m",
    "memory": "512Mi",
    "timeout_seconds": 120
  }
}
```

Rules:

- service node ids use a stable suffix such as `.service`
- recipe steps invoke executable nodes, not service nodes
- BPG provisions required services before scheduling dependent activities
- service nodes still declare IO schemas and side effects for planning and documentation

Example pair:

- `opensearch.service` — container image and connection contract
- `opensearch.hybrid_upsert` — Temporal activity that writes through the service

## Declaring a Temporal activity node

Minimal registry node definition:

```json
{
  "id": "example.greet",
  "version": "0.1.0",
  "capabilities": ["example"],
  "runtime": {
    "type": "temporal_activity",
    "language": "python",
    "entrypoint": "bpg_nodes_example.activities.greet",
    "task_queue": "bpg-example",
    "image": "ghcr.io/example/bpg-nodes-example-worker:0.1.0"
  },
  "io": {
    "input_schema": "schemas/nodes/example.greet.input.schema.json",
    "output_schema": "schemas/nodes/example.greet.output.schema.json"
  },
  "retryable": true,
  "idempotent": true,
  "side_effects": [],
  "execution": {
    "required_secrets": [],
    "required_services": [],
    "requires_network": false,
    "resources": {
      "cpu": "250m",
      "memory": "512Mi",
      "timeout_seconds": 30
    }
  }
}
```

Checklist for node authors:

1. Implement schema-shaped `dict` in, `dict` out activity code.
2. Export the callable from `activities.py`.
3. Add JSON Schema files under `schemas/nodes/`.
4. Add or update `registry/nodes/<package>.json`.
5. Run `python3 scripts/validate_registry.py`.
6. Run `python3 scripts/verify_registry.py --mode runtime-light` when the Python package is installed locally.

## When to use a service node instead

Use a service node when the marketplace entry represents infrastructure that activities depend on, not code you want workflows to call directly.

| Use `temporal_activity` | Use `service_container` |
| --- | --- |
| Custom Python logic | Managed database or search engine |
| Recipe step execution | Dependency provisioning |
| Worker entrypoint required | Container image required, no entrypoint |
| Input/output schemas describe request/response payloads | Schemas describe connection and health contract |

## How BPG binds recipe steps to activity calls

Recipes describe intent. BPG build output describes execution.

Example recipe step:

```json
{
  "id": "verify",
  "select": {
    "node": "audit.verify_chain",
    "version": ">=0.1.0"
  },
  "with": {
    "run_id": "$inputs.run_id"
  }
}
```

During build, BPG:

1. Resolves `audit.verify_chain` to an exact node version and package.
2. Loads the node's input and output schemas.
3. Validates `with` mappings against the input schema and prior step outputs.
4. Records the resolved `runtime.entrypoint`, `runtime.task_queue`, worker image, and required services.
5. Emits a locked execution plan that generated workflow code uses to call the activity with the resolved payload.

At runtime:

- workflow code schedules `audit.verify_chain` on task queue `bpg-audit`
- the worker imports `bpg_nodes_audit.activities.verify_audit_chain`
- the activity receives the schema-shaped payload and returns a schema-shaped result
- downstream steps consume declared output fields such as `verification_valid`

Service dependencies are resolved in the same plan but are provisioned and wired into worker environments rather than invoked as workflow steps.

## Verification modes

The marketplace provides two verification modes via `scripts/verify_registry.py`:

| Context | Mode | Notes |
| --- | --- | --- |
| Marketplace CI | `static` | Validates metadata, schemas, image references, and entrypoint strings |
| Node package repo CI | `runtime-light` | Run after `pip install` of the package; imports entrypoints |
| BPG build flow | `runtime-light` or stricter | Packages available in the build environment |
| Local authoring | `static` always; `runtime-light` when package installed | See commands below |

### Commands

```bash
# Always run in marketplace and node repos
python3 scripts/verify_registry.py --mode static

# Run in node package repo after install
pip install -e .
python3 scripts/verify_registry.py --mode runtime-light
```

### What runtime-light checks

- Python entrypoint importability when the declaring package is installed
- Entrypoint callable shape (when implemented)
- Image reference reachability (optional, when enabled)

Static mode does not import entrypoints. It validates that metadata, schema references, and declared strings are well-formed.

### Expected behavior in this repository

Marketplace CI runs `--mode static` only. Node implementation packages (`bpg_nodes_search`, `bpg_nodes_opensearch`, `bpg_nodes_audit`, and others) are not installed in this repository.

Running `python3 scripts/verify_registry.py --mode runtime-light` locally without those packages installed will report import failures. That is expected behavior, not a marketplace bug. Node package authors should run runtime-light verification in their own repository after `pip install -e .`.

### Future work (BPG repository)

- `bpg marketplace verify` CLI wrapping the library API
- Monorepo CI job that syncs marketplace metadata and runs runtime-light with all packages installed

## Related documentation

- [Composable Nodes and Recipes](composable-nodes-and-recipes.md)
- [Audit Helper Nodes](audit-helper-nodes.md) — real post-run activity examples
- [Capability Taxonomy](capability-taxonomy.md)
- [Contributing](contributing.md)
- Example package layout: [examples/node-authoring/sample-greet-node](../examples/node-authoring/sample-greet-node/README.md)
