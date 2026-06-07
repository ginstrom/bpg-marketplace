from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bpg_marketplace.indexer import build_indexes
from bpg_marketplace.registry import iter_registry_files

from tests.helpers import isolated_repo


class IndexerTests(unittest.TestCase):
    def test_build_indexes_writes_expected_outputs(self):
        with isolated_repo() as repo:
            result = build_indexes(repo)

            generated_dir = repo / "generated"
            self.assertTrue((generated_dir / "manifest.json").exists())
            self.assertTrue((generated_dir / "index.json").exists())
            self.assertTrue((generated_dir / "capabilities.json").exists())
            self.assertTrue((generated_dir / "resolution.json").exists())
            self.assertTrue((generated_dir / "recipes.json").exists())
            self.assertIn(
                "bpg.nodes.weaviate",
                {artifact["id"] for artifact in result["capabilities"]["vector_search"]},
            )
            self.assertIn(
                "bpg.recipes.basic_rag_search",
                {artifact["id"] for artifact in result["capabilities"]["vector_search"]},
            )
            self.assertEqual(result["manifest"]["indexes"]["manifest"], "generated/manifest.json")
            self.assertEqual(result["manifest"]["indexes"]["resolution"], "generated/resolution.json")
            self.assertEqual(
                result["recipes"]["recipes"][0]["id"],
                "bpg.recipes.basic_rag_search",
            )

            index_payload = json.loads((generated_dir / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(len(index_payload["artifacts"]), len(iter_registry_files(repo)))

            manifest_payload = json.loads((generated_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest_payload["artifact_types"][0]["type"], "node_package")
            self.assertEqual(
                manifest_payload["artifact_types"][0]["primary_index"],
                "generated/capabilities.json",
            )
            self.assertEqual(manifest_payload["artifact_types"][1]["type"], "recipe")

    def test_resolution_index_contains_plan_generation_metadata(self):
        with isolated_repo() as repo:
            result = build_indexes(repo)
            resolution = result["resolution"]

            hybrid_search = resolution["capabilities"]["hybrid_search"]
            self.assertIn(
                "opensearch.service",
                {node["id"] for node in hybrid_search["nodes"]},
            )
            self.assertIn(
                "bpg.recipes.opensearch_hybrid_index_japanese_chunk",
                {recipe["id"] for recipe in hybrid_search["recipes"]},
            )

            upsert_versions = resolution["nodes"]["opensearch.hybrid_upsert"]
            self.assertEqual(len(upsert_versions), 1)
            upsert = upsert_versions[0]
            self.assertEqual(upsert["version"], "0.1.0")
            self.assertEqual(upsert["runtime"]["type"], "temporal_activity")
            self.assertEqual(upsert["package_id"], "bpg.nodes.opensearch")
            self.assertEqual(
                upsert["io"]["input_schema"],
                "schemas/nodes/opensearch.hybrid_upsert.input.schema.json",
            )
            self.assertEqual(upsert["execution"]["required_services"], ["opensearch.service"])
            self.assertEqual(
                upsert["execution"]["required_secrets"],
                ["OPENSEARCH_USERNAME", "OPENSEARCH_PASSWORD"],
            )
            self.assertEqual(upsert["worker"]["task_queue"], "bpg-opensearch")

            opensearch_service = resolution["nodes"]["opensearch.service"][0]
            self.assertEqual(opensearch_service["runtime"]["type"], "service_container")
            self.assertEqual(opensearch_service["worker"]["install_mode"], "container")
            self.assertEqual(
                opensearch_service["runtime"]["image"],
                "docker.io/opensearchproject/opensearch:2.14.0",
            )

            recipe = resolution["recipes"]["bpg.recipes.opensearch_hybrid_index_japanese_chunk"]
            upsert_step = next(step for step in recipe["steps"] if step["id"] == "upsert")
            self.assertEqual(upsert_step["select"]["preferred_node"], "opensearch.hybrid_upsert")
            self.assertEqual(
                upsert_step["mappings"]["tokens"],
                {
                    "from": "$.steps.tokenize.token_details",
                    "transform": {
                        "type": "map",
                        "path": "$.surface",
                    },
                },
            )

            resolution_payload = json.loads(
                (repo / "generated" / "resolution.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                resolution_payload["nodes"]["opensearch.hybrid_upsert"][0]["execution"]["required_services"],
                ["opensearch.service"],
            )

    def test_node_level_worker_override_takes_precedence_over_package_default(self):
        """Node-level worker fields must override package defaults in resolution output."""
        with isolated_repo() as repo:
            result = build_indexes(repo)
            opensearch_service = result["resolution"]["nodes"]["opensearch.service"][0]
            package_worker = result["resolution"]["packages"]["bpg.nodes.opensearch"]["worker"]

            self.assertEqual(package_worker["install_mode"], "package")
            self.assertEqual(package_worker["task_queue"], "bpg-opensearch")
            self.assertEqual(
                package_worker["image"],
                "ghcr.io/ginstrom/bpg-nodes-opensearch-worker:0.1.0",
            )

            self.assertEqual(opensearch_service["worker"]["install_mode"], "container")
            self.assertEqual(opensearch_service["worker"]["task_queue"], "bpg-opensearch-service")
            self.assertEqual(
                opensearch_service["worker"]["image"],
                "docker.io/opensearchproject/opensearch:2.14.0",
            )
            self.assertNotEqual(opensearch_service["worker"]["install_mode"], package_worker["install_mode"])
            self.assertNotEqual(opensearch_service["worker"]["task_queue"], package_worker["task_queue"])
