# BPG Marketplace Design Document

## Overview

`bpg-marketplace` is a GitHub-native registry and discovery system for reusable BPG workflow components, operational capabilities, templates, and integrations.

The marketplace is designed for both:

* human developers
* AI coding/orchestration agents

The primary design goal is not visual browsing.

The primary design goal is:

* machine-readable capability discovery
* composable operational workflows
* typed integration metadata
* safe reusable orchestration components

The marketplace is intended to support:

* workflow composition
* AI-assisted development
* operational standardization
* reusable enterprise patterns
* governed automation
* discoverable integrations

---

# Core Philosophy

## Capabilities over packages

The marketplace is capability-oriented rather than package-oriented.

Users and agents should think in terms of:

* vector search
* retrieval
* human approval
* deployment orchestration
* observability
* notifications

Not:

* arbitrary package names

Example:

```text id="v8qudu"
Need:
- hybrid retrieval
- HITL approval
- Kubernetes deployment
```

The marketplace resolves:

* compatible node packages
* templates
* workflow examples
* dependency requirements

---

# Design Goals

## Primary Goals

* Machine-readable discovery
* Typed operational components
* GitHub-native workflow
* Lightweight ecosystem management
* Safe reusable orchestration primitives
* Compatibility metadata
* Observability compatibility
* AI-agent discoverability

---

## Secondary Goals

* Human-readable documentation
* Community contribution workflow
* Verified operational patterns
* Reusable enterprise templates
* Long-term ecosystem growth

---

# Non-Goals

The marketplace is NOT:

* an app store
* a visual drag-and-drop builder
* a centralized execution platform
* a package hosting platform
* a proprietary ecosystem

The marketplace intentionally relies on:

* GitHub
* PyPI
* uv/pip
* standard Python packaging

---

# High-Level Architecture

```text id="wprm5j"
GitHub Repository
    │
    ├── Registry Metadata
    ├── Validation Schemas
    ├── Generated Discovery Index
    ├── Workflow Templates
    ├── Examples
    └── CI Validation
            │
            ▼
Generated JSON Indexes
            │
            ▼
Humans + AI Agents
            │
            ▼
Install Packages from PyPI/GitHub
```

---

# Repository Structure

```text id="txq7nk"
bpg-marketplace/
│
├── registry/
│   ├── nodes/
│   ├── templates/
│   ├── packs/
│   └── policies/
│
├── schemas/
│   ├── node.schema.json
│   ├── template.schema.json
│   ├── pack.schema.json
│   └── policy.schema.json
│
├── generated/
│   ├── index.json
│   ├── capabilities.json
│   ├── templates.json
│   └── compatibility.json
│
├── examples/
│   ├── rag/
│   ├── approvals/
│   ├── devops/
│   └── observability/
│
├── docs/
│   ├── index.md
│   ├── contributing.md
│   ├── trust-levels.md
│   └── capability-taxonomy.md
│
├── scripts/
│   ├── validate_registry.py
│   ├── build_index.py
│   └── verify_packages.py
│
└── .github/
    └── workflows/
```

---

# Marketplace Artifact Types

The marketplace supports multiple artifact types.

---

# 1. Node Packages

Reusable operational primitives.

Examples:

* vector search
* deployment
* notifications
* embeddings
* observability

Example packages:

* `bpg-nodes-weaviate`
* `bpg-nodes-opensearch`
* `bpg-nodes-slack`
* `bpg-nodes-kubernetes`

---

# 2. Workflow Templates

Reusable workflow architectures.

Examples:

* enterprise RAG pipeline
* HITL deployment workflow
* AI review pipeline
* ingestion pipeline
* incident escalation flow

Templates represent:

* reusable operational patterns
* governance best practices
* reference implementations

---

# 3. Capability Packs

Bundled functionality collections.

Examples:

```text id="b0zv8w"
bpg-rag-enterprise
bpg-observability-stack
bpg-ai-delivery
```

These may include:

* node packages
* templates
* policies
* observability integrations

---

# 4. Policies

Reusable operational governance definitions.

Examples:

* approval policies
* retry policies
* escalation policies
* observability requirements

Policies allow organizations to standardize workflow behavior.

---

# Metadata Philosophy

All marketplace artifacts should expose:

* typed metadata
* operational characteristics
* compatibility information
* observability support
* side-effect declarations
* safety properties

This metadata is intended primarily for:

* AI agents
* orchestration systems
* validation tooling
* workflow composition

---

# Node Package Metadata

Example:

```yaml id="vs3ab5"
id: bpg.nodes.weaviate
name: Weaviate Nodes
type: node_package

package:
  python: bpg-nodes-weaviate
  install: "uv add bpg-nodes-weaviate"

source:
  repo: https://github.com/example/bpg-nodes-weaviate

capabilities:
  - vector_search
  - hybrid_search
  - vector_upsert

nodes:
  - id: weaviate.search
    retryable: true
    idempotent: true
    side_effects:
      - network_io

requirements:
  secrets:
    - WEAVIATE_API_KEY

compatibility:
  bpg: ">=0.1.0"

observability:
  traces: true
  metrics: true

trust:
  level: verified
```

---

# Capability Taxonomy

Capabilities should use a standardized taxonomy.

Examples:

```text id="ll2eqk"
vector_search
hybrid_search
embedding_generation
reranking
document_chunking
notification
human_approval
deployment
workflow_pause
workflow_resume
audit_logging
trace_emission
metrics_collection
```

The taxonomy should remain:

* stable
* concise
* machine-readable

---

# Discovery Philosophy

The marketplace should optimize for:

* semantic discovery
* capability matching
* compatibility resolution
* operational safety

Not:

* marketing pages
* screenshots
* visual catalogs

---

# Discovery APIs

The generated index should support queries such as:

```text id="0bjlwm"
Find:
- vector search
- OpenSearch-compatible
- retry-safe
- observable
```

Or:

```text id="xg9m5u"
Find workflow templates:
- RAG
- HITL-enabled
- deployment-ready
```

---

# Generated Indexes

Generated indexes are intended for:

* coding agents
* orchestration tools
* IDE integrations
* workflow generators

Examples:

* `index.json`
* `capabilities.json`
* `templates.json`
* `compatibility.json`

---

# Package Installation Model

The marketplace does not host packages.

Installation uses standard Python tooling.

Examples:

```bash id="p4hjlwm"
uv add bpg-nodes-weaviate
```

Or:

```bash id="d0j6mf"
pip install bpg-nodes-weaviate
```

---

# Plugin Discovery

Packages should self-register using Python entry points.

Example:

```toml id="qny8vr"
[project.entry-points."bpg.nodes"]
weaviate = "bpg_nodes_weaviate:register"
```

This enables:

* automatic node discovery
* runtime registration
* agent introspection

---

# Trust Levels

The marketplace should support multiple trust levels.

---

# Community

* Schema-valid
* Community-maintained
* No guarantees

---

# Verified

* Passes CI validation
* Installation verified
* Smoke tests pass
* Metadata validated

---

# Blessed

* Recommended by BPG maintainers
* Operationally mature
* Production-tested
* Maintained compatibility

---

# Deprecated

* Retained for compatibility
* No longer recommended
* Potential removal in future versions

---

# CI/CD Validation

GitHub Actions should validate:

* metadata schemas
* package installability
* node uniqueness
* compatibility declarations
* capability taxonomy compliance
* example workflows
* template validity

---

# Validation Goals

Validation should ensure:

* ecosystem consistency
* operational safety
* compatibility stability
* discoverability quality

---

# Recommended Validation Categories

## Metadata Validation

* schema compliance
* required fields
* valid identifiers

---

## Installation Validation

* package installs successfully
* dependencies resolve

---

## Workflow Validation

* templates compile
* referenced nodes exist

---

## Safety Validation

* retry semantics declared
* side effects declared
* observability support declared

---

# Long-Term Vision

The marketplace is intended to evolve into:

* a capability registry
* an operational workflow ecosystem
* an AI-agent integration layer
* a reusable enterprise workflow catalog

The long-term value is:

* operational standardization
* reusable governance patterns
* composable AI infrastructure
* machine-readable orchestration ecosystems

Not merely reusable code packages.

---

# Strategic Positioning

The marketplace should be positioned as:

> A machine-readable operational capability ecosystem for AI-native workflow systems.

Not:

* a plugin store
* a no-code marketplace
* a visual automation catalog

The primary audience is:

* developers
* platform engineers
* orchestration systems
* AI coding agents
* enterprise workflow teams

---

# Initial Scope Recommendations

The initial implementation should remain intentionally small.

Recommended first milestone:

* metadata schemas
* registry repository
* generated index
* validation CI
* GitHub Pages documentation
* 2–3 official node packages
* 2–3 workflow templates

The initial focus should prioritize:

* metadata quality
* capability discoverability
* operational consistency
* ecosystem architecture

Over:

* scale
* UI complexity
* monetization
* large package counts

