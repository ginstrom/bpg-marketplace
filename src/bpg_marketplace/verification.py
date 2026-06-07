from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import importlib
import re
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from .registry import iter_registry_files, load_json
from .validation import ValidationIssue, load_schema, validate_artifact, validate_registry


class VerificationMode(str, Enum):
    STATIC = "static"
    RUNTIME_LIGHT = "runtime-light"


@dataclass(frozen=True)
class VerificationIssue:
    artifact_id: str
    artifact_type: str
    path: str
    check: str
    message: str


@dataclass(frozen=True)
class VerificationResult:
    mode: VerificationMode
    issues: list[VerificationIssue]

    @property
    def passed(self) -> bool:
        return not self.issues

    def grouped_by_artifact_id(self) -> dict[str, list[VerificationIssue]]:
        grouped: dict[str, list[VerificationIssue]] = {}
        for issue in self.issues:
            grouped.setdefault(issue.artifact_id, []).append(issue)
        return grouped


_IMAGE_REF_PATTERN = re.compile(
    r"^(?:"
    r"(?P<registry>(?:[a-z0-9]+(?:[._-][a-z0-9]+)*)(?::[0-9]+)?)/"
    r")?"
    r"(?P<name>(?:[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*))"
    r"(?::(?P<tag>[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127})|@(?P<digest>sha256:[a-f0-9]{64}))?"
    r"$"
)

_REGISTRY_ENDPOINTS = {
    "docker.io": "https://registry-1.docker.io/v2/",
    "ghcr.io": "https://ghcr.io/v2/",
}


def _artifact_id(payload: dict) -> str:
    artifact_id = payload.get("id")
    return artifact_id if isinstance(artifact_id, str) else "<unknown>"


def _issue_from_validation(issue: ValidationIssue) -> VerificationIssue:
    payload = load_json(Path(issue.path))
    return VerificationIssue(
        artifact_id=_artifact_id(payload),
        artifact_type=issue.artifact_type,
        path=issue.path,
        check="references",
        message=issue.message,
    )


def _validate_json_schema(artifact_type: str, payload: dict, root: Path) -> list[str]:
    try:
        schema = load_schema(artifact_type, root)
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return [f"schema for '{artifact_type}' is invalid: {exc}"]

    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        errors.append(f"{location}: {error.message}")
    return errors


def _validate_io_schema_ref(root: Path, ref: str) -> str | None:
    path = root / ref
    if not path.exists():
        return f"IO schema '{ref}' does not exist"
    try:
        schema = load_json(path)
    except Exception as exc:  # pragma: no cover - defensive around malformed authored JSON.
        return f"IO schema '{ref}' could not be loaded: {exc}"
    if not isinstance(schema, dict):
        return f"IO schema '{ref}' must contain a JSON object"
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return f"IO schema '{ref}' is not valid JSON Schema: {exc}"
    return None


def _collect_node_io_schema_refs(payload: dict) -> list[tuple[str, str, str]]:
    refs: list[tuple[str, str, str]] = []
    for index, node in enumerate(payload.get("nodes", [])):
        if not isinstance(node, dict):
            continue
        node_id = node.get("id") if isinstance(node.get("id"), str) else f"nodes[{index}]"
        io = node.get("io")
        if not isinstance(io, dict):
            continue
        for key in ["input_schema", "output_schema"]:
            ref = io.get(key)
            if isinstance(ref, str) and ref.strip():
                refs.append((node_id, f"nodes[{index}].io.{key}", ref))
    return refs


def _collect_recipe_referenced_node_ids(artifacts: list[tuple[str, Path, dict[str, Any]]]) -> set[str]:
    referenced: set[str] = set()
    for artifact_type, _path, payload in artifacts:
        if artifact_type != "recipe" or not isinstance(payload.get("steps"), list):
            continue
        for step in payload["steps"]:
            if not isinstance(step, dict):
                continue
            select = step.get("select")
            if not isinstance(select, dict):
                continue
            node_id = select.get("node")
            if isinstance(node_id, str) and node_id.strip():
                referenced.add(node_id)
            preferred_node = select.get("preferred_node")
            if isinstance(preferred_node, str) and preferred_node.strip():
                referenced.add(preferred_node)
    return referenced


def _collect_image_refs(payload: dict) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    worker = payload.get("worker")
    if isinstance(worker, dict):
        image = worker.get("image")
        if isinstance(image, str) and image.strip():
            refs.append(("worker.image", image))

    for index, node in enumerate(payload.get("nodes", [])):
        if not isinstance(node, dict):
            continue
        runtime = node.get("runtime")
        if isinstance(runtime, dict):
            image = runtime.get("image")
            if isinstance(image, str) and image.strip():
                refs.append((f"nodes[{index}].runtime.image", image))
        node_worker = node.get("worker")
        if isinstance(node_worker, dict):
            image = node_worker.get("image")
            if isinstance(image, str) and image.strip():
                refs.append((f"nodes[{index}].worker.image", image))
    return refs


def _validate_image_reference(image: str) -> str | None:
    if not image.strip():
        return "image reference must be a non-empty string"
    if any(char.isspace() for char in image):
        return f"image reference '{image}' must not contain whitespace"
    if _IMAGE_REF_PATTERN.fullmatch(image) is None:
        return f"image reference '{image}' is not a valid container image reference"
    return None


def _registry_host(image: str) -> str:
    first_segment = image.split("/", 1)[0]
    if "." in first_segment or ":" in first_segment:
        return first_segment
    return "docker.io"


def _check_image_reachability(image: str, timeout_seconds: float = 5.0) -> str | None:
    host = _registry_host(image)
    endpoint = _REGISTRY_ENDPOINTS.get(host, f"https://{host}/v2/")
    request = Request(endpoint, method="HEAD")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            if response.status >= 400:
                return f"registry '{host}' returned status {response.status} for '{image}'"
    except URLError as exc:
        return f"registry '{host}' is not reachable for '{image}': {exc.reason}"
    return None


def _verify_entrypoint(entrypoint: str) -> str | None:
    parts = entrypoint.split(".")
    if len(parts) < 2:
        return f"entrypoint '{entrypoint}' is not a valid dotted import path"
    module_name = ".".join(parts[:-1])
    attr_name = parts[-1]
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        return f"entrypoint '{entrypoint}' could not be imported: {exc}"
    if not hasattr(module, attr_name):
        return f"entrypoint '{entrypoint}' attribute '{attr_name}' was not found in '{module_name}'"
    return None


def _append_issue(
    issues: list[VerificationIssue],
    *,
    artifact_id: str,
    artifact_type: str,
    path: str,
    check: str,
    message: str,
) -> None:
    issues.append(
        VerificationIssue(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            path=path,
            check=check,
            message=message,
        )
    )


def verify_registry(
    root: Path | None = None,
    mode: VerificationMode | str = VerificationMode.STATIC,
    *,
    check_image_reachability: bool = False,
    verify_all_entrypoints: bool = False,
) -> VerificationResult:
    if isinstance(mode, str):
        mode = VerificationMode(mode)

    root = root or Path(__file__).resolve().parents[2]
    issues: list[VerificationIssue] = []
    artifacts: list[tuple[str, Path, dict[str, Any]]] = []
    for artifact_type, path in iter_registry_files(root):
        artifacts.append((artifact_type, path, load_json(path)))

    referenced_node_ids = _collect_recipe_referenced_node_ids(artifacts)

    for artifact_type, path, payload in artifacts:
        artifact_id = _artifact_id(payload)
        artifact_path = str(path)

        for message in _validate_json_schema(artifact_type, payload, root):
            _append_issue(
                issues,
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                path=artifact_path,
                check="json_schema",
                message=message,
            )

        for message in validate_artifact(artifact_type, payload):
            _append_issue(
                issues,
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                path=artifact_path,
                check="metadata",
                message=message,
            )

        if artifact_type == "node_package":
            for node_id, field, ref in _collect_node_io_schema_refs(payload):
                schema_path = root / ref
                if schema_path.exists():
                    error = _validate_io_schema_ref(root, ref)
                elif node_id in referenced_node_ids:
                    error = f"IO schema '{ref}' does not exist"
                else:
                    error = None
                if error:
                    _append_issue(
                        issues,
                        artifact_id=artifact_id,
                        artifact_type=artifact_type,
                        path=artifact_path,
                        check="io_schema",
                        message=f"{field}: {error}",
                    )

            for field, image in _collect_image_refs(payload):
                error = _validate_image_reference(image)
                if error:
                    _append_issue(
                        issues,
                        artifact_id=artifact_id,
                        artifact_type=artifact_type,
                        path=artifact_path,
                        check="image_syntax",
                        message=f"{field}: {error}",
                    )
                elif check_image_reachability and mode is VerificationMode.RUNTIME_LIGHT:
                    reachability_error = _check_image_reachability(image)
                    if reachability_error:
                        _append_issue(
                            issues,
                            artifact_id=artifact_id,
                            artifact_type=artifact_type,
                            path=artifact_path,
                            check="image_reachability",
                            message=f"{field}: {reachability_error}",
                        )

            if mode is VerificationMode.RUNTIME_LIGHT:
                for index, node in enumerate(payload.get("nodes", [])):
                    if not isinstance(node, dict):
                        continue
                    node_id = node.get("id")
                    if not verify_all_entrypoints and (
                        not isinstance(node_id, str) or node_id not in referenced_node_ids
                    ):
                        continue
                    runtime = node.get("runtime")
                    if not isinstance(runtime, dict):
                        continue
                    if runtime.get("type") != "temporal_activity":
                        continue
                    if runtime.get("language") != "python":
                        continue
                    entrypoint = runtime.get("entrypoint")
                    if not isinstance(entrypoint, str) or not entrypoint.strip():
                        continue
                    error = _verify_entrypoint(entrypoint)
                    if error:
                        _append_issue(
                            issues,
                            artifact_id=artifact_id,
                            artifact_type=artifact_type,
                            path=artifact_path,
                            check="entrypoint",
                            message=f"nodes[{index}].runtime.entrypoint: {error}",
                        )

    for validation_issue in validate_registry(root):
        issues.append(_issue_from_validation(validation_issue))

    return VerificationResult(mode=mode, issues=issues)
