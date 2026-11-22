"""Files with characters XML does not allow (backlog F4).

LayOut can write control characters (e.g. inside a SketchUp tag name). Reading must
tolerate them; staging files must keep them byte-for-byte.
"""
import hashlib
import unittest
import zipfile

import _support
from _support import ROOT, dm

BROKEN = ROOT / "tests" / "fixtures" / "broken"


class TestPlaceholders(unittest.TestCase):
    def test_round_trip_is_byte_exact(self):
        raw = '<a name="OB\x1f_INSULATION F&amp;B LOW" t="\x01\x0b\x0c"/>'.encode("utf-8") + "é".encode("utf-8")
        hidden = dm._hide_illegal(raw)
        self.assertIsNone(dm.XML_ILLEGAL.search(hidden))
        self.assertEqual(dm._restore_illegal(hidden), raw)

    def test_parsers_accept_it(self):
        raw = b'<a name="OB\x1f_X">t\x1fext</a>'
        self.assertEqual(dm._et_parse(raw).tag, "a")
        self.assertEqual(dm._dom_parse(raw).documentElement.tagName, "a")

    def test_clean_files_untouched(self):
        raw = b'<a name="normal">tab\tnew\nline</a>'
        self.assertIsNone(dm.XML_ILLEGAL.search(raw))
        self.assertEqual(dm._hide_illegal(raw), raw)


@unittest.skipUnless(list(BROKEN.glob("*.layout")), "needs tests/fixtures/broken/*.layout")
class TestRealFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = sorted(BROKEN.glob("*.layout"))[0]
        cls.before = hashlib.sha256(cls.path.read_bytes()).hexdigest()
        dm.index_library(str(BROKEN))
        cls.state = dict(dm.INDEX_STATE)

    @classmethod
    def tearDownClass(cls):
        _support._INDEXED = False

    def test_indexed_without_error(self):
        self.assertEqual(self.state["errors"], [])
        con = dm.DB.connect()
        n = con.execute("SELECT COUNT(*) FROM details WHERE layout_file=?", (str(self.path),)).fetchone()[0]
        con.close()
        self.assertGreater(n, 0)
        self.assertTrue(any("Read tolerantly" in x["message"] for x in dm.read_log_tail(50)))

    def test_staging_keeps_the_characters_byte_for_byte(self):
        with zipfile.ZipFile(self.path) as z:
            bad_pages = {n for n in z.namelist() if n.startswith("pages/") and dm.XML_ILLEGAL.search(z.read(n))}
        self.assertTrue(bad_pages)
        con = dm.DB.connect()
        rows = con.execute(f"SELECT detail_key, page_xml FROM details WHERE layout_file=? AND page_xml IN ({','.join('?' * len(bad_pages))}) ORDER BY group_index",
                           (str(self.path), *bad_pages)).fetchall()
        con.close()
        self.assertTrue(rows)
        kept = 0
        for key, page_xml in rows:
            out = dm.build_staging(key)   # validates the package; raises if it does not read back
            try:
                with zipfile.ZipFile(self.path) as src, zipfile.ZipFile(out) as stg:
                    src_bad = set(dm.XML_ILLEGAL.findall(src.read(page_xml)))
                    stg_page = stg.read(page_xml)
                for b in range(0x20):
                    self.assertNotIn(chr(0xE000 + b).encode("utf-8"), stg_page, "no placeholder may leak into a staging file")
                found = set(dm.XML_ILLEGAL.findall(stg_page))
                self.assertTrue(found <= src_bad)
                if found:
                    kept += 1
                    break
            finally:
                out.unlink(missing_ok=True)
        self.assertEqual(kept, 1, "the detail holding the character keeps it byte-for-byte")

    def test_master_unchanged(self):
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), self.before)


if __name__ == "__main__":
    unittest.main()
