#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bpg_marketplace.verification import VerificationMode, verify_registry


def _format_issues(result) -> str:
    grouped = result.grouped_by_artifact_id()
    lines: list[str] = []
    for artifact_id in sorted(grouped):
        lines.append(f"[{artifact_id}]")
        for issue in grouped[artifact_id]:
            lines.append(f"  {issue.check}: {issue.path}: {issue.message}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify marketplace registry artifacts.")
    parser.add_argument(
        "--mode",
        choices=[mode.value for mode in VerificationMode],
        default=VerificationMode.STATIC.value,
        help="Verification mode. static avoids imports and network checks.",
    )
    parser.add_argument(
        "--check-images",
        action="store_true",
        help="When using runtime-light mode, also check container registry reachability.",
    )
    parser.add_argument(
        "--verify-all-entrypoints",
        action="store_true",
        help="Import every declared Python entrypoint instead of only recipe-referenced nodes.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Optional repository root. Defaults to the marketplace checkout.",
    )
    args = parser.parse_args()

    result = verify_registry(
        root=args.root,
        mode=VerificationMode(args.mode),
        check_image_reachability=args.check_images,
        verify_all_entrypoints=args.verify_all_entrypoints,
    )
    if result.passed:
        print(f"Registry verification passed ({result.mode.value}).")
        return 0

    print(f"Registry verification failed ({result.mode.value}):")
    print(_format_issues(result))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
