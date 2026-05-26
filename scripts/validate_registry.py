#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bpg_marketplace.validation import validate_registry


def main() -> int:
    issues = validate_registry()
    if issues:
        for issue in issues:
            print(f"{issue.path}: {issue.message}")
        return 1

    print("Registry validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
