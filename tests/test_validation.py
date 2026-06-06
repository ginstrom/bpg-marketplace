from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bpg_marketplace.validation import validate_registry

from tests.helpers import isolated_repo


class ValidationTests(unittest.TestCase):
    def test_registry_validation_passes_for_sample_data(self):
        with isolated_repo() as repo:
            self.assertEqual(validate_registry(repo), [])

    def test_registry_validation_reports_duplicate_ids(self):
        with isolated_repo() as repo:
            duplicate_path = repo / "registry" / "nodes" / "duplicate.json"
            payload = json.loads((repo / "registry" / "nodes" / "weaviate.json").read_text(encoding="utf-8"))
            duplicate_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            issues = validate_registry(repo)

            self.assertTrue(any("duplicate artifact id" in issue.message for issue in issues))

    def test_registry_validation_rejects_invalid_recipe(self):
        with isolated_repo() as repo:
            recipe_path = repo / "registry" / "recipes" / "invalid.json"
            payload = json.loads((repo / "registry" / "recipes" / "basic-rag-search.json").read_text(encoding="utf-8"))
            payload["steps"][0]["select"] = {
                "capability": "vector_search",
                "node": "bpg.nodes.weaviate",
            }
            recipe_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            issues = validate_registry(repo)

            self.assertTrue(
                any(
                    issue.artifact_type == "recipe"
                    and "select must specify exactly one of capability or node" in issue.message
                    for issue in issues
                )
            )

    def test_registry_validation_rejects_temporal_activity_without_entrypoint(self):
        with isolated_repo() as repo:
            node_path = repo / "registry" / "nodes" / "bpg-nodes-search.json"
            payload = json.loads(node_path.read_text(encoding="utf-8"))
            del payload["nodes"][0]["runtime"]["entrypoint"]
            node_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            issues = validate_registry(repo)

            self.assertTrue(
                any(
                    issue.artifact_type == "node_package"
                    and "runtime.entrypoint is required for temporal_activity" in issue.message
                    for issue in issues
                )
            )

    def test_registry_validation_rejects_service_container_without_image(self):
        with isolated_repo() as repo:
            node_path = repo / "registry" / "nodes" / "weaviate.json"
            payload = json.loads(node_path.read_text(encoding="utf-8"))
            del payload["nodes"][0]["runtime"]["image"]
            node_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            issues = validate_registry(repo)

            self.assertTrue(
                any(
                    issue.artifact_type == "node_package"
                    and "runtime.image is required for service_container" in issue.message
                    for issue in issues
                )
            )
