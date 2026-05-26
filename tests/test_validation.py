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
