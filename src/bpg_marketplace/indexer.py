from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .registry import generated_root, iter_registry_files, load_json, write_json


def build_indexes(root: Path | None = None) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    capabilities: dict[str, list[dict[str, str]]] = defaultdict(list)
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

        compatibility.append(
            {
                "id": payload["id"],
                "type": payload["type"],
                "compatibility": payload.get("compatibility", {}),
                "trust": payload.get("trust", {}),
            }
        )

    artifacts.sort(key=lambda item: item["id"])
    templates.sort(key=lambda item: item["id"])
    normalized_capabilities = {
        key: sorted(values, key=lambda item: item["id"])
        for key, values in sorted(capabilities.items())
    }

    result = {
        "index": {"artifacts": artifacts},
        "capabilities": normalized_capabilities,
        "templates": {"templates": templates},
        "compatibility": {"artifacts": sorted(compatibility, key=lambda item: item["id"])},
    }

    output_root = generated_root(root)
    write_json(output_root / "index.json", result["index"])
    write_json(output_root / "capabilities.json", result["capabilities"])
    write_json(output_root / "templates.json", result["templates"])
    write_json(output_root / "compatibility.json", result["compatibility"])
    return result
