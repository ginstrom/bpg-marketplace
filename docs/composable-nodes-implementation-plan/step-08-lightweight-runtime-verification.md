# Step 8: Add Lightweight Runtime Verification

## Goal

Provide an authoring-time verification command that checks declared runtime artifacts without executing full workflows.

## Scope

This step adds optional checks suitable for marketplace CI and for [BPG](https://github.com/ginstrom/bpg)'s build flow. It should fail clearly when dependencies are unavailable, but it should not require production infrastructure.

## Tasks

1. Add a verification command or module for marketplace artifacts.
2. Verify registry metadata against JSON Schema.
3. Verify declared IO schema files can be loaded.
4. Verify Python activity entrypoints can be imported when dependencies are installed.
5. Verify container image references are syntactically valid.
6. Optionally verify container image reachability when network access is enabled.
7. Verify recipe references and mappings using the validation from Step 7.
8. Add tests with local dummy entrypoints and intentionally broken entrypoints.

## Verification Modes

Support at least two modes:

- `static`: no network access and no package import beyond local code.
- `runtime-light`: import declared Python entrypoints and optionally check image reachability.

## Acceptance Criteria

- Static verification can run in CI without external services.
- Runtime-light verification can detect a missing Python activity entrypoint.
- Runtime-light verification can detect malformed container image references.
- Verification failures are grouped by artifact ID.
- [BPG](https://github.com/ginstrom/bpg) can call the verification logic through a command or stable library API.

## Notes

This step should not attempt to prove implementation correctness. It verifies that authored metadata points to plausible code and artifacts. Full behavioral testing belongs in node package repositories.
