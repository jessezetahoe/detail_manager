"""Shared test setup.

Importing this module points Detail Manager's app-data folder at a throwaway
temp directory BEFORE detail_manager is imported, so tests never touch the
real %LOCALAPPDATA% index, previews or staging folders.
"""
import atexit
import hashlib
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
FIXTURES = ROOT / "tests" / "fixtures" / "company"
GOLDEN = ROOT / "tests" / "golden"

_APPDATA = tempfile.mkdtemp(prefix="dm_test_appdata_")
# The throwaway data folder (index, previews, staging files) is removed when the run ends.
atexit.register(shutil.rmtree, _APPDATA, True)
os.environ["LOCALAPPDATA"] = _APPDATA
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import detail_manager as dm  # noqa: E402

assert str(dm.DB.root).startswith(_APPDATA), "Tests must not use the real app-data folder"


def fixture_files():
    return sorted(FIXTURES.glob("*.layout")) if FIXTURES.is_dir() else []


def require_fixtures(test):
    return unittest.skipUnless(fixture_files(), "No .layout fixtures in tests/fixtures/company")(test)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse(path: Path):
    """Run the production parser exactly as index_library does."""
    return dm.parse_layout(path, dm.DB.preview_root / (dm.path_key(str(path)) + "_test"))


_INDEXED = False


def ensure_indexed():
    """Index the fixture folder once per test run into the temp DB."""
    global _INDEXED
    if not _INDEXED:
        dm.index_library(str(FIXTURES))
        _INDEXED = True
    return dict(dm.INDEX_STATE)
