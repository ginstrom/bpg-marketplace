#!/usr/bin/env python3
from __future__ import annotations

import filecmp
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bpg_marketplace.indexer import build_indexes


GENERATED_FILES = [
    "index.json",
    "capabilities.json",
    "resolution.json",
    "recipes.json",
    "templates.json",
    "compatibility.json",
    "manifest.json",
]


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp_dir:
        work_root = Path(tmp_dir) / "repo"
        shutil.copytree(repo_root / "registry", work_root / "registry")
        shutil.copytree(repo_root / "schemas", work_root / "schemas")
        generated_root = work_root / "generated"
        snapshot_root = work_root / "snapshot"
        generated_root.mkdir()
        snapshot_root.mkdir()

        build_indexes(work_root)
        for filename in GENERATED_FILES:
            source = generated_root / filename
            if source.exists():
                shutil.copy2(source, snapshot_root / filename)

        for filename in GENERATED_FILES:
            target = generated_root / filename
            if target.exists():
                target.unlink()

        build_indexes(work_root)

        mismatches: list[str] = []
        for filename in GENERATED_FILES:
            first_path = snapshot_root / filename
            second_path = generated_root / filename
            if not first_path.exists() or not second_path.exists():
                mismatches.append(f"missing generated file: {filename}")
                continue
            if not filecmp.cmp(first_path, second_path, shallow=False):
                mismatches.append(filename)

        if mismatches:
            print("Index build is not reproducible. Mismatched files:")
            for item in mismatches:
                print(f"  - {item}")
            return 1

    print("Index build is reproducible.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
