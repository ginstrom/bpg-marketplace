from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from jsonschema.validators import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bpg_marketplace.validation import validate_registry

from tests.helpers import isolated_repo


SAMPLE_NODE_IDS = {
    "embedding.create_text_embedding": "temporal_activity",
    "tokenization.kuromoji_tokenize": "temporal_activity",
    "opensearch.hybrid_upsert": "temporal_activity",
    "opensearch.service": "service_container",
    "weaviate.service": "service_container",
}

JAPANESE_HYBRID_RECIPE_ID = "bpg.recipes.opensearch_hybrid_index_japanese_chunk"
JAPANESE_HYBRID_NODE_REFS = {
    "embedding.create_text_embedding",
    "tokenization.kuromoji_tokenize",
    "opensearch.hybrid_upsert",
}


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

    def test_sample_atomic_search_nodes_have_valid_runtime_and_io_schemas(self):
        with isolated_repo() as repo:
            node_package_schema = json.loads((repo / "schemas" / "node.schema.json").read_text(encoding="utf-8"))
            validator = Draft202012Validator(node_package_schema)
            found: dict[str, dict] = {}
            for path in (repo / "registry" / "nodes").glob("*.json"):
                package = json.loads(path.read_text(encoding="utf-8"))
                if any(node.get("id") in SAMPLE_NODE_IDS for node in package.get("nodes", [])):
                    validator.validate(package)
                for node in package.get("nodes", []):
                    if node.get("id") in SAMPLE_NODE_IDS:
                        found[node["id"]] = node

            self.assertEqual(set(SAMPLE_NODE_IDS), set(found))

            for node_id, expected_runtime in SAMPLE_NODE_IDS.items():
                node = found[node_id]
                self.assertEqual(node["runtime"]["type"], expected_runtime)
                for schema_key in ["input_schema", "output_schema"]:
                    schema_path = repo / node["io"][schema_key]
                    self.assertTrue(schema_path.exists(), f"{node_id} missing {schema_key}: {schema_path}")
                    schema = json.loads(schema_path.read_text(encoding="utf-8"))
                    Draft202012Validator.check_schema(schema)

    def test_japanese_hybrid_indexing_recipe_validates(self):
        with isolated_repo() as repo:
            recipe_schema = json.loads((repo / "schemas" / "recipe.schema.json").read_text(encoding="utf-8"))
            basic_recipe = json.loads(
                (repo / "registry" / "recipes" / "basic-rag-search.json").read_text(encoding="utf-8")
            )
            recipe = json.loads(
                (repo / "registry" / "recipes" / "opensearch-hybrid-index-japanese-chunk.json").read_text(
                    encoding="utf-8"
                )
            )

            Draft202012Validator(recipe_schema).validate(basic_recipe)
            Draft202012Validator(recipe_schema).validate(recipe)
            self.assertEqual(recipe["id"], JAPANESE_HYBRID_RECIPE_ID)
            self.assertEqual(["embed", "tokenize", "upsert"], [step["id"] for step in recipe["steps"]])
            self.assertEqual(basic_recipe["steps"][0]["with"]["query"], "$inputs.query")
            self.assertEqual(
                recipe["steps"][2]["with"]["tokens"],
                {
                    "from": "$.steps.tokenize.token_details",
                    "transform": {
                        "type": "map",
                        "path": "$.surface",
                    },
                },
            )

    def test_recipe_mapping_schema_rejects_unsupported_transform_type(self):
        with isolated_repo() as repo:
            recipe_schema = json.loads((repo / "schemas" / "recipe.schema.json").read_text(encoding="utf-8"))
            recipe_path = repo / "registry" / "recipes" / "opensearch-hybrid-index-japanese-chunk.json"
            recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
            recipe["steps"][2]["with"]["tokens"]["transform"]["type"] = "explode"
            recipe_path.write_text(json.dumps(recipe, indent=2), encoding="utf-8")

            self.assertFalse(Draft202012Validator(recipe_schema).is_valid(recipe))
            issues = validate_registry(repo)
            self.assertTrue(
                any(
                    issue.artifact_type == "recipe"
                    and "steps[2].with.tokens.transform.type must be one of project, map, default, coerce"
                    in issue.message
                    for issue in issues
                )
            )

    def test_recipe_mapping_schema_rejects_empty_source(self):
        with isolated_repo() as repo:
            recipe_schema = json.loads((repo / "schemas" / "recipe.schema.json").read_text(encoding="utf-8"))
            recipe_path = repo / "registry" / "recipes" / "opensearch-hybrid-index-japanese-chunk.json"
            recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
            recipe["steps"][2]["with"]["tokens"]["from"] = ""
            recipe_path.write_text(json.dumps(recipe, indent=2), encoding="utf-8")

            self.assertFalse(Draft202012Validator(recipe_schema).is_valid(recipe))
            issues = validate_registry(repo)
            self.assertTrue(
                any(
                    issue.artifact_type == "recipe"
                    and "steps[2].with.tokens.from must be a non-empty string" in issue.message
                    for issue in issues
                )
            )

    def test_japanese_hybrid_indexing_recipe_references_existing_nodes(self):
        with isolated_repo() as repo:
            recipe = json.loads(
                (repo / "registry" / "recipes" / "opensearch-hybrid-index-japanese-chunk.json").read_text(
                    encoding="utf-8"
                )
            )
            node_ids = set()
            node_capabilities: dict[str, set[str]] = {}
            for path in (repo / "registry" / "nodes").glob("*.json"):
                package = json.loads(path.read_text(encoding="utf-8"))
                for node in package.get("nodes", []):
                    node_ids.add(node["id"])
                    node_capabilities[node["id"]] = set(node.get("capabilities", []))

            preferred_nodes = {
                step["select"]["preferred_node"]
                for step in recipe["steps"]
                if "preferred_node" in step["select"]
            }
            self.assertEqual(JAPANESE_HYBRID_NODE_REFS, preferred_nodes)
            self.assertTrue(preferred_nodes.issubset(node_ids))

            for step in recipe["steps"]:
                preferred_node = step["select"]["preferred_node"]
                capability = step["select"]["capability"]
                self.assertIn(capability, node_capabilities[preferred_node])

    def test_registry_validation_rejects_unknown_exact_recipe_node(self):
        with isolated_repo() as repo:
            recipe_path = repo / "registry" / "recipes" / "basic-rag-search.json"
            recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
            recipe["steps"][0]["select"] = {
                "node": "missing.node",
                "version": ">=0.1.0",
            }
            recipe_path.write_text(json.dumps(recipe, indent=2), encoding="utf-8")

            issues = validate_registry(repo)

            self.assertTrue(
                any(
                    issue.artifact_type == "recipe"
                    and "steps[0].select.node 'missing.node' does not resolve to a node" in issue.message
                    for issue in issues
                )
            )

    def test_registry_validation_rejects_unknown_preferred_recipe_node(self):
        with isolated_repo() as repo:
            recipe_path = repo / "registry" / "recipes" / "basic-rag-search.json"
            recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
            recipe["steps"][0]["select"]["preferred_node"] = "missing.node"
            recipe_path.write_text(json.dumps(recipe, indent=2), encoding="utf-8")

            issues = validate_registry(repo)

            self.assertTrue(
                any(
                    issue.artifact_type == "recipe"
                    and "steps[0].select.preferred_node 'missing.node' does not resolve to a node"
                    in issue.message
                    for issue in issues
                )
            )

    def test_registry_validation_rejects_impossible_recipe_node_version(self):
        with isolated_repo() as repo:
            recipe_path = repo / "registry" / "recipes" / "opensearch-hybrid-index-japanese-chunk.json"
            recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
            recipe["steps"][0]["select"]["version"] = ">=9.0.0"
            recipe_path.write_text(json.dumps(recipe, indent=2), encoding="utf-8")

            issues = validate_registry(repo)

            self.assertTrue(
                any(
                    issue.artifact_type == "recipe"
                    and "steps[0].select.preferred_node 'embedding.create_text_embedding' has no version matching '>=9.0.0'"
                    in issue.message
                    for issue in issues
                )
            )

    def test_registry_validation_rejects_future_step_mapping_reference(self):
        with isolated_repo() as repo:
            recipe_path = repo / "registry" / "recipes" / "opensearch-hybrid-index-japanese-chunk.json"
            recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
            recipe["steps"][0]["with"]["text"] = "$.steps.upsert.result"
            recipe_path.write_text(json.dumps(recipe, indent=2), encoding="utf-8")

            issues = validate_registry(repo)

            self.assertTrue(
                any(
                    issue.artifact_type == "recipe"
                    and "steps[0].with.text: source '$.steps.upsert.result' does not reference a prior step output"
                    in issue.message
                    for issue in issues
                )
            )

    def test_registry_validation_rejects_bad_jsonpath_mapping_reference(self):
        with isolated_repo() as repo:
            recipe_path = repo / "registry" / "recipes" / "opensearch-hybrid-index-japanese-chunk.json"
            recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
            recipe["steps"][0]["with"]["text"] = "$.chunk[0].text"
            recipe_path.write_text(json.dumps(recipe, indent=2), encoding="utf-8")

            issues = validate_registry(repo)

            self.assertTrue(
                any(
                    issue.artifact_type == "recipe"
                    and "steps[0].with.text: source '$.chunk[0].text' is not in the supported JSONPath subset"
                    in issue.message
                    for issue in issues
                )
            )

    def test_registry_validation_rejects_missing_required_node_input(self):
        with isolated_repo() as repo:
            recipe_path = repo / "registry" / "recipes" / "opensearch-hybrid-index-japanese-chunk.json"
            recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
            del recipe["steps"][0]["with"]["model"]
            recipe_path.write_text(json.dumps(recipe, indent=2), encoding="utf-8")

            issues = validate_registry(repo)

            self.assertTrue(
                any(
                    issue.artifact_type == "recipe"
                    and "steps[0].with.model is required by selected node input schema" in issue.message
                    for issue in issues
                )
            )

    def test_registry_validation_rejects_missing_referenced_io_schema(self):
        with isolated_repo() as repo:
            node_path = repo / "registry" / "nodes" / "weaviate.json"
            node_package = json.loads(node_path.read_text(encoding="utf-8"))
            node_package["nodes"][1]["io"]["input_schema"] = "schemas/nodes/missing.schema.json"
            node_path.write_text(json.dumps(node_package, indent=2), encoding="utf-8")

            issues = validate_registry(repo)

            self.assertTrue(
                any(
                    issue.artifact_type == "recipe"
                    and "steps[0].referenced IO schema 'schemas/nodes/missing.schema.json' does not exist"
                    in issue.message
                    for issue in issues
                )
            )

    def test_registry_validation_rejects_incompatible_projection_transform(self):
        with isolated_repo() as repo:
            recipe_path = repo / "registry" / "recipes" / "opensearch-hybrid-index-japanese-chunk.json"
            recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
            recipe["steps"][2]["with"]["tokens"]["transform"]["path"] = "$.position"
            recipe_path.write_text(json.dumps(recipe, indent=2), encoding="utf-8")

            issues = validate_registry(repo)

            self.assertTrue(
                any(
                    issue.artifact_type == "recipe"
                    and "steps[2].with.tokens is incompatible with selected node input schema" in issue.message
                    for issue in issues
                )
            )
