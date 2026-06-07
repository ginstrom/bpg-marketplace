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


def _recipe_step_mappings(step: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mappings: dict[str, dict[str, Any]] = {}
    for target, mapping in step.get("with", {}).items():
        if isinstance(mapping, str):
            mappings[target] = {"from": mapping}
        else:
            mappings[target] = mapping
    return mappings


def _node_resolution_entry(package: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": node["id"],
        "version": node["version"],
        "package_id": package["id"],
        "package_name": package["name"],
        "package_version": package["package"]["version"],
        "capabilities": node.get("capabilities", []),
        "runtime": node.get("runtime", {}),
        "io": node.get("io", {}),
        "execution": node.get("execution", {}),
        "worker": node.get("worker", package.get("worker")),
        "dependencies": {
            "package": package.get("package", {}),
            "artifacts": package.get("dependencies", {}),
        },
        "retryable": node.get("retryable"),
        "idempotent": node.get("idempotent"),
        "side_effects": node.get("side_effects", []),
        "compatibility": package.get("compatibility", {}),
        "trust": package.get("trust", {}),
        "source": package.get("source", {}),
    }


def _recipe_resolution_entry(recipe: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": recipe["id"],
        "version": recipe["version"],
        "name": recipe["name"],
        "summary": recipe["summary"],
        "capabilities": recipe.get("capabilities", []),
        "inputs": recipe.get("inputs", {}),
        "outputs": recipe.get("outputs", {}),
        "defaults": recipe.get("defaults", {}),
        "failure_policy": recipe.get("failure_policy", {}),
        "steps": [
            {
                "id": step["id"],
                "select": step["select"],
                "mappings": _recipe_step_mappings(step),
                "optional": step.get("optional", False),
            }
            for step in recipe.get("steps", [])
        ],
    }


def _build_resolution_index(artifacts: list[dict[str, Any]], recipes: list[dict[str, Any]]) -> dict[str, Any]:
    nodes_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    node_capabilities: dict[str, list[dict[str, Any]]] = defaultdict(list)
    recipe_capabilities: dict[str, list[dict[str, Any]]] = defaultdict(list)
    package_dependencies: dict[str, dict[str, Any]] = {}

    for package in artifacts:
        if package.get("type") != "node_package":
            continue

        package_dependencies[package["id"]] = {
            "package_version": package["package"]["version"],
            "package": package.get("package", {}),
            "dependencies": package.get("dependencies", {}),
            "worker": package.get("worker"),
            "source": package.get("source", {}),
            "compatibility": package.get("compatibility", {}),
            "trust": package.get("trust", {}),
        }

        for node in package.get("nodes", []):
            entry = _node_resolution_entry(package, node)
            nodes_by_id[node["id"]].append(entry)
            for capability in node.get("capabilities", []):
                node_capabilities[capability].append(entry)

    recipe_entries = [_recipe_resolution_entry(recipe) for recipe in recipes]
    for recipe in recipe_entries:
        for capability in recipe.get("capabilities", []):
            recipe_capabilities[capability].append(recipe)

    all_capabilities = sorted(set(node_capabilities) | set(recipe_capabilities))
    capabilities = {
        capability: {
            "nodes": sorted(node_capabilities.get(capability, []), key=lambda item: (item["id"], item["version"])),
            "recipes": sorted(recipe_capabilities.get(capability, []), key=lambda item: (item["id"], item["version"])),
        }
        for capability in all_capabilities
    }

    return {
        "capabilities": capabilities,
        "nodes": {
            node_id: sorted(entries, key=lambda item: item["version"])
            for node_id, entries in sorted(nodes_by_id.items())
        },
        "recipes": {
            recipe["id"]: recipe
            for recipe in sorted(recipe_entries, key=lambda item: item["id"])
        },
        "packages": dict(sorted(package_dependencies.items())),
    }


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
    resolution = _build_resolution_index(artifacts, recipes)

    result = {
        "index": {"artifacts": artifacts},
        "capabilities": normalized_capabilities,
        "resolution": resolution,
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
                "resolution": "generated/resolution.json",
                "recipes": "generated/recipes.json",
                "templates": "generated/templates.json",
                "compatibility": "generated/compatibility.json",
            },
        },
    }

    output_root = generated_root(root)
    write_json(output_root / "index.json", result["index"])
    write_json(output_root / "capabilities.json", result["capabilities"])
    write_json(output_root / "resolution.json", result["resolution"])
    write_json(output_root / "recipes.json", result["recipes"])
    write_json(output_root / "templates.json", result["templates"])
    write_json(output_root / "compatibility.json", result["compatibility"])
    write_json(output_root / "manifest.json", result["manifest"])
    return result
