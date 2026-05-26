from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .registry import iter_registry_files, load_json


@dataclass(frozen=True)
class ValidationIssue:
    artifact_type: str
    path: str
    message: str


def load_schema(artifact_type: str, root: Path | None = None) -> dict:
    filename = {
        "node_package": "node.schema.json",
        "template": "template.schema.json",
        "pack": "pack.schema.json",
        "policy": "policy.schema.json",
    }[artifact_type]
    schema_path = (root or Path(__file__).resolve().parents[2]) / "schemas" / filename
    return load_json(schema_path)


def _require_fields(payload: dict, fields: list[str]) -> list[str]:
    return [field for field in fields if field not in payload]


def _validate_common(payload: dict, expected_type: str) -> list[str]:
    errors: list[str] = []
    missing = _require_fields(payload, ["id", "name", "type", "compatibility", "trust"])
    if missing:
        errors.append(f"missing required field(s): {', '.join(missing)}")
        return errors
    if payload["type"] != expected_type:
        errors.append(f"type must be '{expected_type}'")
    if not isinstance(payload["id"], str) or not payload["id"].startswith("bpg."):
        errors.append("id must be a string starting with 'bpg.'")
    if not isinstance(payload["name"], str) or not payload["name"].strip():
        errors.append("name must be a non-empty string")
    compatibility = payload.get("compatibility")
    if not isinstance(compatibility, dict) or "bpg" not in compatibility:
        errors.append("compatibility.bpg is required")
    trust = payload.get("trust")
    if not isinstance(trust, dict) or trust.get("level") not in {
        "community",
        "verified",
        "blessed",
        "deprecated",
    }:
        errors.append("trust.level must be one of community, verified, blessed, deprecated")
    return errors


def _validate_capabilities(payload: dict) -> list[str]:
    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        return ["capabilities must be a non-empty array"]
    if not all(isinstance(item, str) and item for item in capabilities):
        return ["capabilities entries must be non-empty strings"]
    return []


def _validate_node_package(payload: dict) -> list[str]:
    errors = _validate_common(payload, "node_package")
    errors.extend(_validate_capabilities(payload))
    package = payload.get("package")
    if not isinstance(package, dict) or not package.get("python") or not package.get("install"):
        errors.append("package.python and package.install are required")
    source = payload.get("source")
    if not isinstance(source, dict) or not source.get("repo"):
        errors.append("source.repo is required")
    nodes = payload.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        errors.append("nodes must be a non-empty array")
    observability = payload.get("observability")
    if not isinstance(observability, dict) or not {
        "traces",
        "metrics",
    }.issubset(observability):
        errors.append("observability.traces and observability.metrics are required")
    return errors


def _validate_template(payload: dict) -> list[str]:
    errors = _validate_common(payload, "template")
    errors.extend(_validate_capabilities(payload))
    if not payload.get("summary"):
        errors.append("summary is required")
    references = payload.get("references")
    if not isinstance(references, dict):
        errors.append("references are required")
    else:
        if not references.get("example_path"):
            errors.append("references.example_path is required")
        if not isinstance(references.get("required_nodes"), list):
            errors.append("references.required_nodes must be an array")
    return errors


def _validate_pack(payload: dict) -> list[str]:
    errors = _validate_common(payload, "pack")
    errors.extend(_validate_capabilities(payload))
    if not payload.get("summary"):
        errors.append("summary is required")
    includes = payload.get("includes")
    if not isinstance(includes, list) or not includes:
        errors.append("includes must be a non-empty array")
    return errors


def _validate_policy(payload: dict) -> list[str]:
    errors = _validate_common(payload, "policy")
    errors.extend(_validate_capabilities(payload))
    if not payload.get("summary"):
        errors.append("summary is required")
    rules = payload.get("rules")
    if not isinstance(rules, list) or not rules:
        errors.append("rules must be a non-empty array")
    return errors


def validate_artifact(artifact_type: str, payload: dict) -> list[str]:
    validators = {
        "node_package": _validate_node_package,
        "template": _validate_template,
        "pack": _validate_pack,
        "policy": _validate_policy,
    }
    return validators[artifact_type](payload)


def validate_registry(root: Path | None = None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    seen_ids: dict[str, str] = {}

    for artifact_type, path in iter_registry_files(root):
        payload = load_json(path)
        for message in validate_artifact(artifact_type, payload):
            issues.append(
                ValidationIssue(
                    artifact_type=artifact_type,
                    path=str(path),
                    message=message,
                )
            )

        artifact_id = payload.get("id")
        if artifact_id:
            previous = seen_ids.get(artifact_id)
            if previous:
                issues.append(
                    ValidationIssue(
                        artifact_type=artifact_type,
                        path=str(path),
                        message=f"duplicate artifact id '{artifact_id}' already seen in {previous}",
                    )
                )
            seen_ids[artifact_id] = str(path)

    return issues
