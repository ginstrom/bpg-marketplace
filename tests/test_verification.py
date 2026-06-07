from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "fixtures"))

from bpg_marketplace.verification import VerificationMode, verify_registry

from tests.helpers import isolated_repo


def _write_dummy_node_package(repo: Path) -> None:
    node_path = repo / "registry" / "nodes" / "dummy-node.json"
    node_path.write_text(
        json.dumps(
            {
                "capabilities": ["dummy"],
                "compatibility": {"bpg": ">=0.1.0"},
                "dependencies": {"python": [{"name": "dummy-entrypoints", "version": "0.1.0"}]},
                "id": "bpg.nodes.dummy",
                "name": "Dummy Node Package",
                "nodes": [
                    {
                        "capabilities": ["dummy"],
                        "execution": {
                            "required_secrets": [],
                            "required_services": [],
                            "requires_network": False,
                            "resources": {
                                "cpu": "250m",
                                "memory": "512Mi",
                                "timeout_seconds": 30,
                            },
                        },
                        "id": "dummy.activity",
                        "idempotent": True,
                        "io": {
                            "input_schema": "schemas/nodes/embedding.create_text_embedding.input.schema.json",
                            "output_schema": "schemas/nodes/embedding.create_text_embedding.output.schema.json",
                        },
                        "retryable": True,
                        "runtime": {
                            "entrypoint": "dummy_entrypoints.activities.dummy_activity",
                            "image": "ghcr.io/example/dummy-worker:0.1.0",
                            "language": "python",
                            "task_queue": "dummy",
                            "type": "temporal_activity",
                        },
                        "side_effects": [],
                        "version": "0.1.0",
                    }
                ],
                "observability": {"metrics": True, "traces": True},
                "package": {
                    "install": "pip install dummy-entrypoints==0.1.0",
                    "python": "dummy_entrypoints",
                    "version": "0.1.0",
                },
                "source": {"repo": "https://example.com/dummy"},
                "trust": {"level": "community"},
                "type": "node_package",
                "worker": {
                    "image": "ghcr.io/example/dummy-worker:0.1.0",
                    "install_mode": "package",
                    "task_queue": "dummy",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _keep_only_dummy_node_package(repo: Path) -> None:
    nodes_dir = repo / "registry" / "nodes"
    for path in nodes_dir.glob("*.json"):
        if path.name != "dummy-node.json":
            path.unlink()


def _remove_recipes_except(repo: Path, recipe_names: set[str]) -> None:
    recipes_dir = repo / "registry" / "recipes"
    for path in recipes_dir.glob("*.json"):
        if path.name not in recipe_names:
            path.unlink()


class VerificationTests(unittest.TestCase):
    def test_static_verification_passes_for_sample_data(self):
        with isolated_repo() as repo:
            result = verify_registry(repo, mode=VerificationMode.STATIC)

            self.assertTrue(result.passed)
            self.assertEqual([], result.issues)

    def test_static_verification_detects_invalid_json_schema(self):
        with isolated_repo() as repo:
            recipe_path = repo / "registry" / "recipes" / "basic-rag-search.json"
            recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
            recipe["type"] = "not-a-recipe"
            recipe_path.write_text(json.dumps(recipe, indent=2), encoding="utf-8")

            result = verify_registry(repo, mode=VerificationMode.STATIC)

            self.assertFalse(result.passed)
            grouped = result.grouped_by_artifact_id()
            self.assertIn(recipe["id"], grouped)
            self.assertTrue(any(issue.check == "json_schema" for issue in grouped[recipe["id"]]))

    def test_static_verification_detects_missing_io_schema(self):
        with isolated_repo() as repo:
            node_path = repo / "registry" / "nodes" / "weaviate.json"
            node_package = json.loads(node_path.read_text(encoding="utf-8"))
            node_package["nodes"][1]["io"]["input_schema"] = "schemas/nodes/missing.schema.json"
            node_path.write_text(json.dumps(node_package, indent=2), encoding="utf-8")

            result = verify_registry(repo, mode=VerificationMode.STATIC)

            self.assertFalse(result.passed)
            grouped = result.grouped_by_artifact_id()
            self.assertIn(node_package["id"], grouped)
            self.assertTrue(any(issue.check == "io_schema" for issue in grouped[node_package["id"]]))

    def test_runtime_light_verification_detects_malformed_image_reference(self):
        with isolated_repo() as repo:
            node_path = repo / "registry" / "nodes" / "weaviate.json"
            node_package = json.loads(node_path.read_text(encoding="utf-8"))
            node_package["nodes"][0]["runtime"]["image"] = "not valid image"
            node_path.write_text(json.dumps(node_package, indent=2), encoding="utf-8")

            result = verify_registry(repo, mode=VerificationMode.RUNTIME_LIGHT)

            self.assertFalse(result.passed)
            grouped = result.grouped_by_artifact_id()
            self.assertIn(node_package["id"], grouped)
            self.assertTrue(any(issue.check == "image_syntax" for issue in grouped[node_package["id"]]))

    def test_runtime_light_verification_imports_dummy_entrypoint(self):
        with isolated_repo() as repo:
            _write_dummy_node_package(repo)
            _keep_only_dummy_node_package(repo)
            _remove_recipes_except(repo, set())

            result = verify_registry(
                repo,
                mode=VerificationMode.RUNTIME_LIGHT,
                verify_all_entrypoints=True,
            )

            self.assertTrue(result.passed)

    def test_runtime_light_verification_detects_missing_entrypoint(self):
        with isolated_repo() as repo:
            _write_dummy_node_package(repo)
            node_package = json.loads((repo / "registry" / "nodes" / "dummy-node.json").read_text(encoding="utf-8"))
            node_package["nodes"][0]["runtime"]["entrypoint"] = "dummy_entrypoints.activities.missing_activity"
            (repo / "registry" / "nodes" / "dummy-node.json").write_text(
                json.dumps(node_package, indent=2),
                encoding="utf-8",
            )
            _keep_only_dummy_node_package(repo)
            _remove_recipes_except(repo, set())

            result = verify_registry(
                repo,
                mode=VerificationMode.RUNTIME_LIGHT,
                verify_all_entrypoints=True,
            )

            self.assertFalse(result.passed)
            grouped = result.grouped_by_artifact_id()
            self.assertIn("bpg.nodes.dummy", grouped)
            self.assertTrue(any(issue.check == "entrypoint" for issue in grouped["bpg.nodes.dummy"]))

    def test_runtime_light_verification_groups_failures_by_artifact_id(self):
        with isolated_repo() as repo:
            recipe_path = repo / "registry" / "recipes" / "dummy-recipe.json"
            recipe_path.write_text(
                json.dumps(
                    {
                        "capabilities": ["dummy"],
                        "defaults": {},
                        "failure_policy": {"mode": "fail_fast"},
                        "id": "bpg.recipes.dummy",
                        "inputs": {"value": {"type": "string"}},
                        "name": "Dummy Recipe",
                        "outputs": {"result": {"type": "string"}},
                        "steps": [
                            {
                                "id": "run",
                                "select": {
                                    "capability": "dummy",
                                    "preferred_node": "dummy.activity",
                                },
                                "with": {
                                    "value": "hello",
                                },
                            }
                        ],
                        "summary": "Dummy recipe for verification tests",
                        "tradeoffs": [],
                        "type": "recipe",
                        "version": "0.1.0",
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            _write_dummy_node_package(repo)
            node_package = json.loads((repo / "registry" / "nodes" / "dummy-node.json").read_text(encoding="utf-8"))
            node_package["nodes"][0]["io"]["input_schema"] = "schemas/nodes/missing.schema.json"
            node_package["nodes"][0]["runtime"]["entrypoint"] = "dummy_entrypoints.activities.missing_activity"
            node_package["nodes"][0]["runtime"]["image"] = "bad image"
            (repo / "registry" / "nodes" / "dummy-node.json").write_text(
                json.dumps(node_package, indent=2),
                encoding="utf-8",
            )
            _keep_only_dummy_node_package(repo)
            _remove_recipes_except(repo, {"dummy-recipe.json"})

            result = verify_registry(
                repo,
                mode=VerificationMode.RUNTIME_LIGHT,
                verify_all_entrypoints=True,
            )
            grouped = result.grouped_by_artifact_id()

            self.assertIn("bpg.nodes.dummy", grouped)
            checks = {issue.check for issue in grouped["bpg.nodes.dummy"]}
            self.assertTrue({"io_schema", "image_syntax", "entrypoint"}.issubset(checks))

    @patch("bpg_marketplace.verification._check_image_reachability")
    def test_runtime_light_verification_can_check_image_reachability(self, reachability_mock):
        reachability_mock.return_value = "registry 'ghcr.io' is not reachable for 'ghcr.io/example/dummy-worker:0.1.0': unreachable"
        with isolated_repo() as repo:
            _write_dummy_node_package(repo)
            _keep_only_dummy_node_package(repo)
            _remove_recipes_except(repo, set())

            result = verify_registry(
                repo,
                mode=VerificationMode.RUNTIME_LIGHT,
                check_image_reachability=True,
                verify_all_entrypoints=True,
            )

            self.assertFalse(result.passed)
            grouped = result.grouped_by_artifact_id()
            self.assertTrue(any(issue.check == "image_reachability" for issue in grouped["bpg.nodes.dummy"]))
