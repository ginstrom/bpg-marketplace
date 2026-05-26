#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bpg_marketplace.registry import iter_registry_files, load_json


def main() -> int:
    package_count = 0
    for artifact_type, path in iter_registry_files():
        if artifact_type != "node_package":
            continue
        package = load_json(path).get("package", {})
        python_package = package.get("python")
        install_command = package.get("install")
        if not python_package or not install_command:
            print(f"{path}: missing package.python or package.install")
            return 1
        package_count += 1

    print(f"Verified package metadata for {package_count} node package(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
