from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


class IndexReproducibilityTests(unittest.TestCase):
    def test_index_build_is_reproducible(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "check_index_reproducibility.py"
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
