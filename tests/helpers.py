from __future__ import annotations

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def isolated_repo():
    source_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_root = Path(tmp_dir) / "repo"
        shutil.copytree(source_root, target_root)
        yield target_root
