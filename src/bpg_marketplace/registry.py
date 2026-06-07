from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ARTIFACT_DIRS = {
    "node_package": "nodes",
    "recipe": "recipes",
    "template": "templates",
    "pack": "packs",
    "policy": "policies",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def registry_root(root: Path | None = None) -> Path:
    return (root or repo_root()) / "registry"


def schema_root(root: Path | None = None) -> Path:
    return (root or repo_root()) / "schemas"


def generated_root(root: Path | None = None) -> Path:
    return (root or repo_root()) / "generated"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def iter_registry_files(root: Path | None = None) -> list[tuple[str, Path]]:
    base = registry_root(root)
    files: list[tuple[str, Path]] = []
    for artifact_type, directory in ARTIFACT_DIRS.items():
        for path in sorted((base / directory).glob("*.json")):
            files.append((artifact_type, path))
    return files
