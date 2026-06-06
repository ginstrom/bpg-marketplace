from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .registry import (
    ARTIFACT_DIRS,
    generated_root,
    iter_registry_files,
    load_json,
    registry_root,
    schema_root,
    write_json,
)


def build_indexes(root: Path | None = None) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    capabilities: dict[str, list[dict[str, str]]] = defaultdict(list)
    recipes: list[dict[str, Any]] = []
    templates: list[dict[str, Any]] = []
    compatibility: list[dict[str, Any]] = []

    for artifact_type, path in iter_registry_files(root):
        payload = load_json(path)
        payload["_source"] = str(path)
        artifacts.append(payload)

        for capability in payload.get("capabilities", []):
            capabilities[capability].append(
                {
                    "id": payload["id"],
                    "type": payload["type"],
                    "name": payload["name"],
                }
            )

        if artifact_type == "template":
            templates.append(payload)
        if artifact_type == "recipe":
            recipes.append(payload)

        compatibility.append(
            {
                "id": payload["id"],
                "type": payload["type"],
                "compatibility": payload.get("compatibility", {}),
                "trust": payload.get("trust", {}),
            }
        )

    artifacts.sort(key=lambda item: item["id"])
    recipes.sort(key=lambda item: item["id"])
    templates.sort(key=lambda item: item["id"])
    normalized_capabilities = {
        key: sorted(values, key=lambda item: item["id"])
        for key, values in sorted(capabilities.items())
    }

    result = {
        "index": {"artifacts": artifacts},
        "capabilities": normalized_capabilities,
        "recipes": {"recipes": recipes},
        "templates": {"templates": templates},
        "compatibility": {"artifacts": sorted(compatibility, key=lambda item: item["id"])},
        "manifest": {
            "artifact_types": [
                {
                    "type": artifact_type,
                    "directory": str(registry_root(root) / directory),
                    "schema": str(schema_root(root) / f"{artifact_type.removesuffix('_package')}.schema.json"),
                    "primary_index": (
                        "generated/templates.json"
                        if artifact_type == "template"
                        else "generated/recipes.json"
                        if artifact_type == "recipe"
                        else "generated/capabilities.json"
                        if artifact_type == "node_package"
                        else "generated/index.json"
                    ),
                }
                for artifact_type, directory in ARTIFACT_DIRS.items()
            ],
            "indexes": {
                "manifest": "generated/manifest.json",
                "index": "generated/index.json",
                "capabilities": "generated/capabilities.json",
                "recipes": "generated/recipes.json",
                "templates": "generated/templates.json",
                "compatibility": "generated/compatibility.json",
            },
        },
    }

    output_root = generated_root(root)
    write_json(output_root / "index.json", result["index"])
    write_json(output_root / "capabilities.json", result["capabilities"])
    write_json(output_root / "recipes.json", result["recipes"])
    write_json(output_root / "templates.json", result["templates"])
    write_json(output_root / "compatibility.json", result["compatibility"])
    write_json(output_root / "manifest.json", result["manifest"])
    return result
