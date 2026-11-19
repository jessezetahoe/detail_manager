"""Masters are never modified by indexing or staging (handoff section 46).

Named to sort last so it also catches anything earlier test files did.
"""
import unittest

import _support
from _support import dm, ensure_indexed, fixture_files, require_fixtures, sha256_file


@require_fixtures
class TestZReadOnly(unittest.TestCase):
    def test_masters_unchanged(self):
        watched = fixture_files() + sorted((_support.ROOT / "tests" / "fixtures" / "projects").glob("*.layout"))
        before = {p: (sha256_file(p), p.stat().st_mtime_ns, p.stat().st_size) for p in watched}
        _support._INDEXED = False
        ensure_indexed()
        con = dm.DB.connect()
        keys = [r[0] for r in con.execute("SELECT detail_key FROM details GROUP BY layout_file")]
        con.close()
        for k in keys:
            dm.build_staging(k).unlink()
        after = {p: (sha256_file(p), p.stat().st_mtime_ns, p.stat().st_size) for p in watched}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
