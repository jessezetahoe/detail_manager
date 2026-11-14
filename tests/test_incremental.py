"""Incremental index refresh (handoff sections 13, 33). Uses its own temp library."""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import _support
from _support import dm, fixture_files, require_fixtures


@require_fixtures
class TestIncremental(unittest.TestCase):
    def setUp(self):
        self.lib = Path(tempfile.mkdtemp(prefix="dm_test_lib_"))
        smallest = min(fixture_files(), key=lambda p: p.stat().st_size)
        self.copy = self.lib / smallest.name
        shutil.copy2(smallest, self.copy)

    def tearDown(self):
        shutil.rmtree(self.lib, ignore_errors=True)
        _support._INDEXED = False  # this test replaced the index; others re-index fixtures

    def run_index(self):
        dm.index_library(str(self.lib))
        return dict(dm.INDEX_STATE)

    def details_for(self, path):
        con = dm.DB.connect()
        n = con.execute("SELECT COUNT(*) FROM details WHERE layout_file=?", (str(path),)).fetchone()[0]
        con.close()
        return n

    def test_refresh_cycle(self):
        s = self.run_index()
        self.assertEqual((s["changed"], s["unchanged"], s["errors"]), (1, 0, []))
        n = self.details_for(self.copy)
        self.assertGreater(n, 0)

        s = self.run_index()
        self.assertEqual((s["changed"], s["unchanged"]), (0, 1), "unchanged master must be skipped")

        st = self.copy.stat()
        os.utime(self.copy, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))
        s = self.run_index()
        self.assertEqual((s["changed"], s["unchanged"]), (1, 0), "changed mtime must reindex")
        self.assertEqual(self.details_for(self.copy), n)

        bad = self.lib / "broken.layout"
        bad.write_bytes(b"not a zip file")
        s = self.run_index()
        self.assertEqual(len(s["errors"]), 1, "broken master reported")
        self.assertEqual(self.details_for(self.copy), n, "broken master must not affect others")
        con = dm.DB.connect()
        err = con.execute("SELECT last_error FROM layout_files WHERE layout_file=?", (str(bad),)).fetchone()[0]
        con.close()
        self.assertTrue(err)

        self.copy.unlink()
        self.run_index()
        self.assertEqual(self.details_for(self.copy), 0, "deleted master removed from index")


if __name__ == "__main__":
    unittest.main()
