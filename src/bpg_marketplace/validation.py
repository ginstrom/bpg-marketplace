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
        "recipe": "recipe.schema.json",
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
    if (
        not isinstance(package, dict)
        or not package.get("python")
        or not package.get("install")
        or not package.get("version")
    ):
        errors.append("package.python, package.install, and package.version are required")
    source = payload.get("source")
    if not isinstance(source, dict) or not source.get("repo"):
        errors.append("source.repo is required")
    if "worker" in payload:
        errors.extend(_validate_worker(payload["worker"], "worker"))
    if "dependencies" in payload and not isinstance(payload["dependencies"], dict):
        errors.append("dependencies must be an object")
    nodes = payload.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        errors.append("nodes must be a non-empty array")
    else:
        node_ids: set[str] = set()
        package_capabilities = set(payload.get("capabilities", []))
        for index, node in enumerate(nodes):
            prefix = f"nodes[{index}]"
            if not isinstance(node, dict):
                errors.append(f"{prefix} must be an object")
                continue
            node_id = node.get("id")
            if not isinstance(node_id, str) or not node_id.strip():
                errors.append(f"{prefix}.id must be a non-empty string")
            elif node_id in node_ids:
                errors.append(f"{prefix}.id '{node_id}' is duplicated in package")
            else:
                node_ids.add(node_id)
            if not isinstance(node.get("version"), str) or not node.get("version", "").strip():
                errors.append(f"{prefix}.version must be a non-empty string")
            capabilities = node.get("capabilities")
            if not isinstance(capabilities, list) or not capabilities:
                errors.append(f"{prefix}.capabilities must be a non-empty array")
            elif not all(isinstance(item, str) and item for item in capabilities):
                errors.append(f"{prefix}.capabilities entries must be non-empty strings")
            elif package_capabilities and not set(capabilities).issubset(package_capabilities):
                errors.append(f"{prefix}.capabilities must be declared by the package")
            errors.extend(_validate_runtime(node.get("runtime"), prefix))
            errors.extend(_validate_io(node.get("io"), prefix))
            if not isinstance(node.get("retryable"), bool):
                errors.append(f"{prefix}.retryable must be a boolean")
            if not isinstance(node.get("idempotent"), bool):
                errors.append(f"{prefix}.idempotent must be a boolean")
            if not isinstance(node.get("side_effects"), list):
                errors.append(f"{prefix}.side_effects must be an array")
            errors.extend(_validate_execution(node.get("execution"), prefix))
            if "worker" in node:
                errors.extend(_validate_worker(node["worker"], f"{prefix}.worker"))
    observability = payload.get("observability")
    if not isinstance(observability, dict) or not {
        "traces",
        "metrics",
    }.issubset(observability):
        errors.append("observability.traces and observability.metrics are required")
    return errors


def _validate_worker(worker: object, prefix: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(worker, dict):
        return [f"{prefix} must be an object"]
    if not isinstance(worker.get("image"), str) or not worker.get("image", "").strip():
        errors.append(f"{prefix}.image must be a non-empty string")
    if worker.get("install_mode") not in {"package", "container", "external"}:
        errors.append(f"{prefix}.install_mode must be one of package, container, external")
    if "task_queue" in worker and (
        not isinstance(worker["task_queue"], str) or not worker["task_queue"].strip()
    ):
        errors.append(f"{prefix}.task_queue must be a non-empty string")
    return errors


def _validate_runtime(runtime: object, prefix: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(runtime, dict):
        return [f"{prefix}.runtime must be an object"]
    runtime_type = runtime.get("type")
    if runtime_type not in {"temporal_activity", "service_container", "external_service"}:
        errors.append(
            f"{prefix}.runtime.type must be one of temporal_activity, service_container, external_service"
        )
        return errors
    if runtime_type == "temporal_activity":
        for key in ["language", "entrypoint"]:
            if not isinstance(runtime.get(key), str) or not runtime.get(key, "").strip():
                errors.append(f"{prefix}.runtime.{key} is required for temporal_activity")
    if runtime_type == "service_container" and (
        not isinstance(runtime.get("image"), str) or not runtime.get("image", "").strip()
    ):
        errors.append(f"{prefix}.runtime.image is required for service_container")
    for key in ["language", "entrypoint", "task_queue", "image"]:
        if key in runtime and (not isinstance(runtime[key], str) or not runtime[key].strip()):
            errors.append(f"{prefix}.runtime.{key} must be a non-empty string")
    return errors


def _validate_io(io: object, prefix: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(io, dict):
        return [f"{prefix}.io must be an object"]
    for key in ["input_schema", "output_schema"]:
        if not isinstance(io.get(key), str) or not io.get(key, "").strip():
            errors.append(f"{prefix}.io.{key} must be a non-empty string")
    return errors


def _validate_execution(execution: object, prefix: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(execution, dict):
        return [f"{prefix}.execution must be an object"]
    if not isinstance(execution.get("requires_network"), bool):
        errors.append(f"{prefix}.execution.requires_network must be a boolean")
    resources = execution.get("resources")
    if not isinstance(resources, dict):
        errors.append(f"{prefix}.execution.resources must be an object")
    else:
        for key in ["cpu", "memory"]:
            if not isinstance(resources.get(key), str) or not resources.get(key, "").strip():
                errors.append(f"{prefix}.execution.resources.{key} must be a non-empty string")
        if "timeout_seconds" in resources and (
            not isinstance(resources["timeout_seconds"], int) or resources["timeout_seconds"] < 1
        ):
            errors.append(f"{prefix}.execution.resources.timeout_seconds must be a positive integer")
    for key in ["required_secrets", "required_services"]:
        value = execution.get(key)
        if not isinstance(value, list):
            errors.append(f"{prefix}.execution.{key} must be an array")
        elif not all(isinstance(item, str) and item for item in value):
            errors.append(f"{prefix}.execution.{key} entries must be non-empty strings")
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


def _validate_recipe(payload: dict) -> list[str]:
    errors: list[str] = []
    missing = _require_fields(
        payload,
        [
            "id",
            "type",
            "name",
            "summary",
            "version",
            "capabilities",
            "inputs",
            "outputs",
            "steps",
            "defaults",
            "failure_policy",
            "tradeoffs",
        ],
    )
    if missing:
        errors.append(f"missing required field(s): {', '.join(missing)}")
        return errors

    if payload["type"] != "recipe":
        errors.append("type must be 'recipe'")
    if not isinstance(payload["id"], str) or not payload["id"].startswith("bpg."):
        errors.append("id must be a string starting with 'bpg.'")
    if not isinstance(payload["name"], str) or not payload["name"].strip():
        errors.append("name must be a non-empty string")
    if not isinstance(payload["summary"], str) or not payload["summary"].strip():
        errors.append("summary is required")
    if not isinstance(payload["version"], str) or not payload["version"].strip():
        errors.append("version must be a non-empty string")
    errors.extend(_validate_capabilities(payload))

    if not isinstance(payload.get("inputs"), dict):
        errors.append("inputs must be an object")
    if not isinstance(payload.get("outputs"), dict):
        errors.append("outputs must be an object")
    if not isinstance(payload.get("defaults"), dict):
        errors.append("defaults must be an object")
    if not isinstance(payload.get("failure_policy"), dict):
        errors.append("failure_policy must be an object")
    if not isinstance(payload.get("tradeoffs"), list):
        errors.append("tradeoffs must be an array")

    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append("steps must be a non-empty array")
        return errors

    for index, step in enumerate(steps):
        prefix = f"steps[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if not isinstance(step.get("id"), str) or not step.get("id", "").strip():
            errors.append(f"{prefix}.id must be a non-empty string")
        select = step.get("select")
        if not isinstance(select, dict):
            errors.append(f"{prefix}.select must be an object")
            continue
        has_capability = "capability" in select
        has_node = "node" in select
        if has_capability == has_node:
            errors.append(f"{prefix}.select must specify exactly one of capability or node")
        for key in ["capability", "node", "preferred_node", "version"]:
            if key in select and (not isinstance(select[key], str) or not select[key].strip()):
                errors.append(f"{prefix}.select.{key} must be a non-empty string")
        if "with" in step:
            if not isinstance(step["with"], dict):
                errors.append(f"{prefix}.with must be an object")
            else:
                errors.extend(_validate_recipe_step_mappings(prefix, step["with"]))
        if "optional" in step and not isinstance(step["optional"], bool):
            errors.append(f"{prefix}.optional must be a boolean")

    return errors


def _validate_recipe_step_mappings(prefix: str, mappings: dict) -> list[str]:
    errors: list[str] = []
    for field_name, mapping in mappings.items():
        field_prefix = f"{prefix}.with.{field_name}"
        if isinstance(mapping, str):
            if not mapping.strip():
                errors.append(f"{field_prefix} must be a non-empty string or mapping object")
            continue
        if not isinstance(mapping, dict):
            errors.append(f"{field_prefix} must be a non-empty string or mapping object")
            continue

        source = mapping.get("from")
        if not isinstance(source, str) or not source.strip():
            errors.append(f"{field_prefix}.from must be a non-empty string")
        allowed_mapping_keys = {"from", "transform"}
        for key in mapping:
            if key not in allowed_mapping_keys:
                errors.append(f"{field_prefix}.{key} is not supported")

        if "transform" in mapping:
            errors.extend(_validate_recipe_mapping_transform(field_prefix, mapping["transform"]))

    return errors


def _validate_recipe_mapping_transform(prefix: str, transform: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(transform, dict):
        return [f"{prefix}.transform must be an object"]

    transform_type = transform.get("type")
    if transform_type not in {"project", "map", "default", "coerce"}:
        errors.append(f"{prefix}.transform.type must be one of project, map, default, coerce")
        return errors

    required_keys = {
        "project": {"type", "path"},
        "map": {"type", "path"},
        "default": {"type", "value"},
        "coerce": {"type", "to"},
    }[transform_type]
    allowed_keys = required_keys

    for key in required_keys:
        if key not in transform:
            errors.append(f"{prefix}.transform.{key} is required for {transform_type}")
    for key in transform:
        if key not in allowed_keys:
            errors.append(f"{prefix}.transform.{key} is not supported for {transform_type}")

    if transform_type in {"project", "map"}:
        path = transform.get("path")
        if not isinstance(path, str) or not path.strip():
            errors.append(f"{prefix}.transform.path must be a non-empty string")
    if transform_type == "coerce" and transform.get("to") not in {"string", "number", "integer", "boolean"}:
        errors.append(f"{prefix}.transform.to must be one of string, number, integer, boolean")

    return errors


def validate_artifact(artifact_type: str, payload: dict) -> list[str]:
    validators = {
        "node_package": _validate_node_package,
        "recipe": _validate_recipe,
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
