from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from .registry import iter_registry_files, load_json


@dataclass(frozen=True)
class ValidationIssue:
    artifact_type: str
    path: str
    message: str


@dataclass(frozen=True)
class NodeRecord:
    node: dict


@dataclass(frozen=True)
class MappingSource:
    root: str
    path: list[str]


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
        if isinstance(select.get("version"), str):
            version_error = _validate_version_constraint(select["version"])
            if version_error:
                errors.append(f"{prefix}.select.version {version_error}")
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


_VERSION_CLAUSE_RE = re.compile(
    r"^(>=|<=|>|<|==|=)?\s*v?(\d+(?:\.\d+){0,2})(?:[-+].*)?$"
)


def _parse_version(version: str) -> tuple[int, ...] | None:
    match = re.match(r"^v?(\d+(?:\.\d+){0,2})(?:[-+].*)?$", version)
    if not match:
        return None
    parts = tuple(int(part) for part in match.group(1).split("."))
    return parts + (0,) * (3 - len(parts))


def _version_clause_matches(version_parts: tuple[int, ...], clause: str) -> bool:
    match = _VERSION_CLAUSE_RE.match(clause.strip())
    if not match:
        return False
    operator = match.group(1) or "=="
    expected_parts = _parse_version(match.group(2))
    if expected_parts is None:
        return False
    if operator in {"=", "=="}:
        return version_parts == expected_parts
    if operator == ">=":
        return version_parts >= expected_parts
    if operator == "<=":
        return version_parts <= expected_parts
    if operator == ">":
        return version_parts > expected_parts
    if operator == "<":
        return version_parts < expected_parts
    return False


def _validate_version_constraint(constraint: str) -> str | None:
    """Return an error message when a version constraint uses unsupported syntax."""
    stripped = constraint.strip()
    if not stripped:
        return None
    clauses = [part.strip() for part in stripped.split(",") if part.strip()]
    if not clauses:
        return None
    for clause in clauses:
        if not _VERSION_CLAUSE_RE.match(clause):
            return (
                "version constraint must use comma-separated clauses with operators "
                ">=, <=, >, <, ==, or ="
            )
    return None


def _version_matches(version: str, constraint: str | None) -> bool:
    if not constraint:
        return True
    version_parts = _parse_version(version)
    constraint = constraint.strip()
    if not constraint:
        return True
    clauses = [part.strip() for part in constraint.split(",") if part.strip()]
    if not clauses:
        return True
    if version_parts is None:
        return version == constraint
    if len(clauses) == 1 and not _VERSION_CLAUSE_RE.match(clauses[0]):
        return version == constraint
    return all(_version_clause_matches(version_parts, clause) for clause in clauses)


def _build_node_catalog(
    artifacts: list[tuple[str, Path, dict]],
) -> tuple[dict[str, list[NodeRecord]], dict[str, list[NodeRecord]]]:
    by_id: dict[str, list[NodeRecord]] = {}
    by_capability: dict[str, list[NodeRecord]] = {}
    for artifact_type, path, payload in artifacts:
        if artifact_type != "node_package":
            continue
        for node in payload.get("nodes", []):
            if not isinstance(node, dict) or not isinstance(node.get("id"), str):
                continue
            record = NodeRecord(node=node)
            by_id.setdefault(node["id"], []).append(record)
            for capability in node.get("capabilities", []):
                if isinstance(capability, str):
                    by_capability.setdefault(capability, []).append(record)
    return by_id, by_capability


def _load_schema_ref(root: Path, ref: str) -> tuple[dict | None, str | None]:
    path = root / ref
    if not path.exists():
        return None, f"referenced IO schema '{ref}' does not exist"
    try:
        schema = load_json(path)
    except Exception as exc:  # pragma: no cover - defensive around malformed authored JSON.
        return None, f"referenced IO schema '{ref}' could not be loaded: {exc}"
    if not isinstance(schema, dict):
        return None, f"referenced IO schema '{ref}' must contain a JSON object"
    return schema, None


def _schema_type(schema: dict | None) -> str | list[str] | None:
    if not isinstance(schema, dict):
        return None
    if "const" in schema:
        return _json_type_name(schema["const"])
    if "enum" in schema and schema["enum"]:
        return _json_type_name(schema["enum"][0])
    return schema.get("type")


def _json_type_name(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "null"


def _type_set(schema: dict | None) -> set[str]:
    schema_type = _schema_type(schema)
    if isinstance(schema_type, str):
        return {schema_type}
    if isinstance(schema_type, list):
        return {item for item in schema_type if isinstance(item, str)}
    return set()


def _types_compatible(source: dict | None, target: dict | None) -> bool:
    source_types = _type_set(source)
    target_types = _type_set(target)
    if not source_types or not target_types:
        return True
    if source_types & target_types:
        if "array" in source_types and "array" in target_types:
            return _types_compatible(
                source.get("items") if source else None,
                target.get("items") if target else None,
            )
        return True
    if source_types == {"integer"} and "number" in target_types:
        return True
    return False


def _schema_at_path(schema: dict | None, path: list[str]) -> dict | None:
    current = schema
    for segment in path:
        if not isinstance(current, dict):
            return None
        if _schema_type(current) == "array":
            current = current.get("items")
        if not isinstance(current, dict):
            return None
        properties = current.get("properties")
        if not isinstance(properties, dict) or segment not in properties:
            return None
        current = properties[segment]
    return current if isinstance(current, dict) else None


def _parse_mapping_source(value: str) -> MappingSource | None:
    if not value.startswith("$"):
        return None
    if value.startswith("$inputs."):
        raw = value.removeprefix("$inputs.")
        root = "inputs"
    elif value.startswith("$.steps."):
        raw = value.removeprefix("$.steps.")
        root = "steps"
    elif value.startswith("$."):
        raw = value.removeprefix("$.")
        root = "inputs"
    else:
        return None
    if not raw:
        return None
    parts = raw.split(".")
    if not all(re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", part) for part in parts):
        return None
    return MappingSource(root=root, path=parts)


def _literal_schema(value: Any) -> dict:
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int) and not isinstance(value, bool):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        return {"type": "array"}
    if isinstance(value, dict):
        return {"type": "object"}
    return {}


def _apply_transform_schema(source_schema: dict | None, transform: object) -> dict | None:
    if not isinstance(transform, dict):
        return source_schema
    transform_type = transform.get("type")
    if transform_type == "map":
        if not isinstance(source_schema, dict) or _schema_type(source_schema) != "array":
            return None
        item_schema = source_schema.get("items")
        projected = _schema_at_path(item_schema if isinstance(item_schema, dict) else None, _transform_path(transform))
        return {"type": "array", "items": projected} if projected else None
    if transform_type == "project":
        return _schema_at_path(source_schema, _transform_path(transform))
    if transform_type == "default":
        return _literal_schema(transform.get("value"))
    if transform_type == "coerce":
        target_type = transform.get("to")
        return {"type": target_type} if isinstance(target_type, str) else None
    return None


def _transform_path(transform: dict) -> list[str]:
    path = transform.get("path")
    if not isinstance(path, str):
        return []
    if path.startswith("$."):
        path = path[2:]
    return [part for part in path.split(".") if part]


def _recipe_input_root_schema(recipe: dict) -> dict:
    inputs = recipe.get("inputs")
    return {
        "type": "object",
        "properties": inputs if isinstance(inputs, dict) else {},
    }


def _resolve_step_records(
    recipe: dict,
    step: dict,
    by_id: dict[str, list[NodeRecord]],
    by_capability: dict[str, list[NodeRecord]],
) -> tuple[list[NodeRecord], list[str]]:
    errors: list[str] = []
    select = step.get("select")
    if not isinstance(select, dict):
        return [], errors

    version_constraint = select.get("version") if isinstance(select.get("version"), str) else None
    if "node" in select:
        node_id = select.get("node")
        records = list(by_id.get(node_id, []))
        if not records:
            errors.append(f"select.node '{node_id}' does not resolve to a node")
            return [], errors
        matches = [record for record in records if _version_matches(record.node.get("version", ""), version_constraint)]
        if not matches:
            errors.append(
                f"select.node '{node_id}' has no version matching '{version_constraint}'"
            )
        return matches, errors

    capability = select.get("capability")
    records = list(by_capability.get(capability, []))
    if not records:
        errors.append(f"select.capability '{capability}' does not resolve to any node")
        return [], errors

    preferred_node = select.get("preferred_node")
    if preferred_node:
        preferred_records = list(by_id.get(preferred_node, []))
        if not preferred_records:
            errors.append(f"select.preferred_node '{preferred_node}' does not resolve to a node")
            return [], errors
        if not any(capability in record.node.get("capabilities", []) for record in preferred_records):
            errors.append(
                f"select.preferred_node '{preferred_node}' does not provide capability '{capability}'"
            )
            return [], errors
        records = preferred_records

    matches = [
        record
        for record in records
        if capability in record.node.get("capabilities", [])
        and _version_matches(record.node.get("version", ""), version_constraint)
    ]
    if not matches:
        target = f"preferred_node '{preferred_node}'" if preferred_node else f"capability '{capability}'"
        errors.append(f"select.{target} has no version matching '{version_constraint}'")
    return matches, errors


def _source_schema_for_mapping(
    source: str,
    recipe: dict,
    prior_outputs: dict[str, dict],
) -> tuple[dict | None, str | None]:
    parsed = _parse_mapping_source(source)
    if not parsed:
        return None, f"source '{source}' is not in the supported JSONPath subset"

    if parsed.root == "inputs":
        input_name = parsed.path[0]
        input_schema = _schema_at_path(_recipe_input_root_schema(recipe), [input_name])
        if input_schema is None:
            return None, f"source '{source}' does not reference a declared recipe input"
        return _schema_at_path(input_schema, parsed.path[1:]) if len(parsed.path) > 1 else input_schema, None

    step_id = parsed.path[0]
    if step_id not in prior_outputs:
        return None, f"source '{source}' does not reference a prior step output"
    output_schema = prior_outputs[step_id]
    field_schema = _schema_at_path(output_schema, parsed.path[1:])
    if field_schema is None:
        return None, f"source '{source}' does not exist in step '{step_id}' output schema"
    return field_schema, None


def _validate_step_mapping_compatibility(
    recipe: dict,
    step: dict,
    step_index: int,
    input_schema: dict,
    prior_outputs: dict[str, dict],
) -> list[str]:
    errors: list[str] = []
    mappings = step.get("with", {})
    mappings = mappings if isinstance(mappings, dict) else {}
    target_properties = input_schema.get("properties") if isinstance(input_schema, dict) else {}
    target_properties = target_properties if isinstance(target_properties, dict) else {}
    required = input_schema.get("required") if isinstance(input_schema, dict) else []
    required = required if isinstance(required, list) else []

    for field in required:
        if isinstance(field, str) and field not in mappings:
            errors.append(f"steps[{step_index}].with.{field} is required by selected node input schema")

    for field, mapping in mappings.items():
        target_schema = target_properties.get(field)
        if target_schema is None:
            continue
        field_prefix = f"steps[{step_index}].with.{field}"
        if isinstance(mapping, str) and mapping.startswith("$"):
            source_schema, error = _source_schema_for_mapping(mapping, recipe, prior_outputs)
            if error:
                errors.append(f"{field_prefix}: {error}")
                continue
            mapped_schema = source_schema
        elif isinstance(mapping, dict):
            source = mapping.get("from")
            if not isinstance(source, str):
                continue
            source_schema, error = _source_schema_for_mapping(source, recipe, prior_outputs)
            if error:
                errors.append(f"{field_prefix}: {error}")
                continue
            mapped_schema = _apply_transform_schema(source_schema, mapping.get("transform"))
            if mapped_schema is None:
                errors.append(f"{field_prefix}.transform is incompatible with source '{source}'")
                continue
        else:
            mapped_schema = _literal_schema(mapping)

        if not _types_compatible(mapped_schema, target_schema):
            errors.append(f"{field_prefix} is incompatible with selected node input schema")

    return errors


def _validate_registry_references(
    root: Path,
    artifacts: list[tuple[str, Path, dict]],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    by_id, by_capability = _build_node_catalog(artifacts)
    service_nodes = {
        node_id
        for node_id, records in by_id.items()
        if any(record.node.get("runtime", {}).get("type") == "service_container" for record in records)
    }

    for artifact_type, path, recipe in artifacts:
        if artifact_type != "recipe" or not isinstance(recipe.get("steps"), list):
            continue
        prior_outputs: dict[str, dict] = {}
        for step_index, step in enumerate(recipe["steps"]):
            if not isinstance(step, dict):
                continue
            records, errors = _resolve_step_records(recipe, step, by_id, by_capability)
            for error in errors:
                issues.append(ValidationIssue("recipe", str(path), f"steps[{step_index}].{error}"))
            if not records:
                continue

            selected = records[0]
            io = selected.node.get("io") if isinstance(selected.node.get("io"), dict) else {}
            input_schema_ref = io.get("input_schema")
            output_schema_ref = io.get("output_schema")
            input_schema: dict | None = None
            output_schema: dict | None = None
            if isinstance(input_schema_ref, str):
                input_schema, error = _load_schema_ref(root, input_schema_ref)
                if error:
                    issues.append(ValidationIssue("recipe", str(path), f"steps[{step_index}].{error}"))
            if isinstance(output_schema_ref, str):
                output_schema, error = _load_schema_ref(root, output_schema_ref)
                if error:
                    issues.append(ValidationIssue("recipe", str(path), f"steps[{step_index}].{error}"))

            for service in selected.node.get("execution", {}).get("required_services", []):
                if service not in service_nodes:
                    issues.append(
                        ValidationIssue(
                            "recipe",
                            str(path),
                            f"steps[{step_index}].execution.required_services '{service}' does not resolve to a service_container node",
                        )
                    )

            if input_schema:
                for error in _validate_step_mapping_compatibility(
                    recipe,
                    step,
                    step_index,
                    input_schema,
                    prior_outputs,
                ):
                    issues.append(ValidationIssue("recipe", str(path), error))
            if output_schema and isinstance(step.get("id"), str):
                prior_outputs[step["id"]] = output_schema
    return issues


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
    root = root or Path(__file__).resolve().parents[2]
    artifacts: list[tuple[str, Path, dict]] = []

    for artifact_type, path in iter_registry_files(root):
        payload = load_json(path)
        artifacts.append((artifact_type, path, payload))
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

    issues.extend(_validate_registry_references(root, artifacts))
    return issues
