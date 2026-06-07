"""Minimal example node implementation."""

from __future__ import annotations

from typing import Any

from bpg_sdk import node
from bpg_sdk.manifest import Idempotency, RetrySafety, SideEffects

_PKG = "bpg.nodes.example@v1"


@node(
    package=_PKG,
    node_id="example.greet",
    input_schema={
        "type": "object",
        "additionalProperties": False,
        "properties": {"name": {"type": "string", "minLength": 1}},
        "required": ["name"],
    },
    output_schema={
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "message": {"type": "string"},
            "greeted": {"type": "boolean"},
        },
        "required": ["message", "greeted"],
    },
    capabilities=["example"],
    side_effects=SideEffects.NONE,
    idempotency=Idempotency.IDEMPOTENT,
    retry_safety=RetrySafety.SAFE,
)
def greet(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name", "")).strip()
    if not name:
        raise ValueError("example.greet requires name")
    return {"message": f"Hello, {name}", "greeted": True}
