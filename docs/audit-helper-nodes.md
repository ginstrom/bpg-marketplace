# Audit Helper Nodes

Optional marketplace nodes for post-run audit export, verification, compliance reporting, and evidence routing.

## Runtime capture stays mandatory

BPG captures audit records in the runtime. The Postgres audit ledger, OpenTelemetry traces, and local `events.jsonl` replay log are written independently of marketplace nodes.

These helper nodes are **reporting and export utilities**. Users can omit them without disabling core audit capture. Do not use marketplace nodes as the primary implementation for:

- `log_every_node_to_audit`
- `record_approval_for_compliance`
- `trace_workflow`

Those responsibilities belong in the BPG runtime.

## Package

Registry package: `bpg.nodes.audit`

Install:

```bash
uv add bpg-nodes-audit
```

## Helper nodes

| Node | Purpose |
| --- | --- |
| `audit.export_bundle` | Export a deterministic audit evidence bundle for one run |
| `audit.verify_chain` | Verify hash-chain integrity for one run |
| `audit.write_compliance_summary` | Render a markdown or JSON compliance summary |
| `audit.notify_compliance_channel` | Route a summary to Slack, email, or webhook |
| `audit.create_case` | Open a compliance case ticket for one run |
| `audit.attach_evidence` | Attach exported evidence to an existing case |

## Required environment

Nodes that query the audit ledger require Postgres access:

```bash
export BPG_AUDIT_DATABASE_URL=postgresql://bpg:bpg@localhost:55432/bpg
```

Nodes may also accept `dsn` or `dsn_env` in their input payload.

Notification nodes reuse the same environment conventions as communication nodes:

- `SLACK_BOT_TOKEN` for Slack delivery
- `SMTP_HOST`, `SMTP_FROM`, and related SMTP settings for email delivery
- `COMPLIANCE_WEBHOOK_URL` or `webhook_url` input for webhook delivery

## Post-run workflow pattern

Compose helper nodes after normal workflow execution:

```text
business_workflow -> verify_audit_chain -> export_audit_bundle -> write_compliance_summary -> notify_compliance_channel
```

The sample recipe `bpg.recipes.post_run_audit_reporting` covers verify, export, and summarize steps. Add notification or case-management nodes only when your compliance process needs them.

## Example process

See [examples/observability/post-run-audit-reporting.v2.bpg.yaml](../examples/observability/post-run-audit-reporting.v2.bpg.yaml).

## Related documentation

- [BPG CLI: bpg audit](https://github.com/ginstrom/bpg/blob/main/docs/cli/audit.md)
- [Traceability and Auditability Design](https://github.com/ginstrom/bpg/blob/main/docs/design/traceability-and-auditability.md)
