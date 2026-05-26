#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bpg_marketplace.indexer import build_indexes


def main() -> int:
    result = build_indexes()
    print(f"Built index for {len(result['index']['artifacts'])} artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
