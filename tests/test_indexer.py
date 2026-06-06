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
