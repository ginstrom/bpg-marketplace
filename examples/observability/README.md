# Observability Examples

Examples for post-run audit reporting and compliance helper workflows.

Runtime audit capture is mandatory and independent of these examples. The workflows below assume a completed run already exists in the Postgres audit ledger.

## Examples

- `post-run-audit-reporting.v2.bpg.yaml` — verify, export, and summarize audit evidence for one `run_id`

## Prerequisites

```bash
export BPG_AUDIT_DATABASE_URL=postgresql://bpg:bpg@localhost:55432/bpg
uv add bpg-nodes-audit
```

## Suggested flow

1. Run a normal business workflow with runtime audit capture enabled.
2. Copy the resulting `run_id`.
3. Run the post-run reporting process with that `run_id` as input.

```bash
uv run bpg doctor examples/observability/post-run-audit-reporting.v2.bpg.yaml
```
