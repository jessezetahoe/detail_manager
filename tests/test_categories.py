"""Sidebar categories from the scrapbook number (backlog U2)."""
import json
import tempfile
import unittest
from pathlib import Path

from _support import dm, ensure_indexed, require_fixtures


class TestCategoryRules(unittest.TestCase):
    def test_shipped_file_matches_built_in_list(self):
        raw = json.loads(dm.categories_path().read_text(encoding="utf-8"))
        self.assertEqual(dm._validate_categories(raw), dm._validate_categories(dm.DEFAULT_CATEGORIES))

    def test_mapping(self):
        f = dm.category_for_filename
        self.assertEqual(f("(01) FND CMU CONT.layout"), ("Foundation", ""))
        self.assertEqual(f("(04) FLR TO 2PLY BEAM HYD FLSH EXT SJ.layout"), ("Floor to Beam", "Flush, Exterior"))
        self.assertEqual(f("(07) FLR TO STL BEAM TRAD BEAR INT SJ.layout"), ("Floor to Beam", "Bearing, Interior"))
        self.assertEqual(f("(10) ROOF RDGE TRAD SOLD RFTR.layout"), ("Roof", ""))
        self.assertEqual(f("(4) ODD SPELLING.layout"), ("Floor to Beam", "Flush, Exterior"))
        self.assertEqual(f("PAGE TEMPLATE.layout"), ("Other", ""))
        self.assertEqual(f("(99) NEW TYPE.layout"), ("Other", ""))

    def test_parent_matches_every_sub_type(self):
        m = dm.category_matches
        self.assertTrue(m("(04) X.layout", "Floor to Beam"))
        self.assertTrue(m("(07) X.layout", "Floor to Beam"))
        self.assertTrue(m("(04) X.layout", "Floor to Beam|Flush, Exterior"))
        self.assertFalse(m("(05) X.layout", "Floor to Beam|Flush, Exterior"))
        self.assertFalse(m("(10) X.layout", "Roof|"))

    def test_broken_file_falls_back_and_is_logged(self):
        real = dm.categories_path
        tmp = Path(tempfile.mkdtemp()) / "categories.json"
        try:
            dm.categories_path = lambda: tmp
            for bad in ("{ not json", '{"categories": []}', '{"categories": [{"name": "X"}]}', '{"categories": [{"name": "X", "numbers": ["a"]}]}'):
                with self.subTest(bad=bad):
                    tmp.write_text(bad, encoding="utf-8")
                    dm._CATEGORY_CACHE["cats"] = None
                    self.assertEqual(dm.categories_config(), dm._validate_categories(dm.DEFAULT_CATEGORIES))
                    self.assertTrue(dm._CATEGORY_CACHE["error"])
            self.assertIn("categories.json could not be used", dm.read_log_tail(5)[-1]["message"])
            tmp.write_text(json.dumps({"categories": [{"numbers": ["13"], "name": "Standards"}]}), encoding="utf-8")
            dm._CATEGORY_CACHE["cats"] = None
            self.assertEqual(dm.category_for_filename("(13) ZE STD KING STUD.layout"), ("Standards", ""))
            tmp.unlink()
            dm._CATEGORY_CACHE["cats"] = None
            self.assertEqual(dm.category_for_filename("(13) X.layout"), ("ZE Standards", ""))
        finally:
            dm.categories_path = real
            dm._CATEGORY_CACHE["cats"] = None


@require_fixtures
class TestCategoryIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_indexed()

    def test_sidebar_groups_and_counts(self):
        groups = dm.library_categories()
        counts = {g["name"]: g["count"] for g in groups}
        self.assertEqual(counts, {"Foundation": 28, "Floor to Foundation": 84, "Floor to Floor": 28, "ZE Standards": 4, "Connections": 5})
        self.assertEqual([g["name"] for g in groups][0], "Foundation")  # file order kept
        self.assertEqual(sum(counts.values()), 149)

    def test_search_within_category(self):
        r = dm.search_details("", category="ZE Standards")
        self.assertEqual(len(r), 4)
        self.assertTrue(all(x["layout_filename"].startswith("(13)") for x in r))
        self.assertTrue(dm.search_details("king", category="ZE Standards"))
        self.assertEqual(dm.search_details("king", category="Foundation"), [])
        self.assertEqual(dm.search_details("", category="Floor to Beam"), [])
        self.assertEqual(dm.search_details("", category="No Such Category"), [])

    def test_page_has_new_sidebar(self):
        for needle in ('data-cat=""', 'id="cats"', "Source files (advanced)", "Library and admin tools", 'id="filterlabel"', "&category="):
            self.assertIn(needle, dm.INDEX_HTML)
        self.assertNotIn('class="notice"', dm.INDEX_HTML)


if __name__ == "__main__":
    unittest.main()
