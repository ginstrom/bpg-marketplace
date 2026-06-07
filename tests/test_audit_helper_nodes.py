from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from jsonschema.validators import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bpg_marketplace.validation import validate_registry

from tests.helpers import isolated_repo


AUDIT_NODE_IDS = {
    "audit.export_bundle",
    "audit.verify_chain",
    "audit.write_compliance_summary",
    "audit.notify_compliance_channel",
    "audit.create_case",
    "audit.attach_evidence",
}


class AuditHelperNodeRegistryTests(unittest.TestCase):
    def test_registry_validation_passes_with_audit_helper_nodes(self):
        with isolated_repo() as repo:
            self.assertEqual(validate_registry(repo), [])

    def test_audit_node_package_declares_helper_nodes(self):
        with isolated_repo() as repo:
            payload = json.loads(
                (repo / "registry" / "nodes" / "bpg-nodes-audit.json").read_text(encoding="utf-8")
            )
            helper_node_ids = {
                node["id"]
                for node in payload["nodes"]
                if node.get("runtime", {}).get("type") == "temporal_activity"
            }
            self.assertEqual(helper_node_ids, AUDIT_NODE_IDS)
            service_nodes = [node for node in payload["nodes"] if node["id"] == "postgres_audit.service"]
            self.assertEqual(len(service_nodes), 1)
            self.assertEqual(service_nodes[0]["runtime"]["type"], "service_container")
            ledger_nodes = [
                node
                for node in payload["nodes"]
                if "postgres_audit.service" in node.get("execution", {}).get("required_services", [])
            ]
            self.assertGreaterEqual(len(ledger_nodes), 3)

    def test_audit_node_io_schemas_are_valid_json_schema(self):
        with isolated_repo() as repo:
            for node_id in sorted(AUDIT_NODE_IDS):
                for direction in ("input", "output"):
                    schema_path = repo / "schemas" / "nodes" / f"{node_id}.{direction}.schema.json"
                    schema = json.loads(schema_path.read_text(encoding="utf-8"))
                    Draft202012Validator.check_schema(schema)

    def test_post_run_audit_reporting_recipe_references_audit_nodes(self):
        with isolated_repo() as repo:
            payload = json.loads(
                (repo / "registry" / "recipes" / "post-run-audit-reporting.json").read_text(encoding="utf-8")
            )
            selected_nodes = {step["select"]["node"] for step in payload["steps"]}
            self.assertEqual(
                selected_nodes,
                {
                    "audit.verify_chain",
                    "audit.export_bundle",
                    "audit.write_compliance_summary",
                },
            )

    def test_observability_pack_includes_audit_helpers(self):
        with isolated_repo() as repo:
            payload = json.loads(
                (repo / "registry" / "packs" / "observability-stack.json").read_text(encoding="utf-8")
            )
            self.assertIn("bpg.nodes.audit", payload["includes"])
            self.assertIn("bpg.recipes.post_run_audit_reporting", payload["includes"])
