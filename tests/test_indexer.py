from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bpg_marketplace.indexer import build_indexes

from tests.helpers import isolated_repo


class IndexerTests(unittest.TestCase):
    def test_build_indexes_writes_expected_outputs(self):
        with isolated_repo() as repo:
            result = build_indexes(repo)

            generated_dir = repo / "generated"
            self.assertTrue((generated_dir / "index.json").exists())
            self.assertTrue((generated_dir / "capabilities.json").exists())
            self.assertEqual(result["capabilities"]["vector_search"][0]["id"], "bpg.nodes.weaviate")

            index_payload = json.loads((generated_dir / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(len(index_payload["artifacts"]), 4)
