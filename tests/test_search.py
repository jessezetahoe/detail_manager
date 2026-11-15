"""Search behavior (handoff section 17)."""
import unittest
from pathlib import Path

from _support import dm, ensure_indexed, require_fixtures


def names(results):
    return [Path(r["layout_file"]).name for r in results]


@require_fixtures
class TestSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_indexed()

    def test_raw_abbreviation(self):
        self.assertIn("(02) FLR TO FND CONC HYD TJI.layout", names(dm.search_details("TJI")))

    def test_expanded_abbreviation(self):
        self.assertIn("(02) FLR TO FND CONC HYD TJI.layout", names(dm.search_details("I-Joist")))

    def test_scene_terms(self):
        r = dm.search_details("grade beam garage")
        self.assertTrue(r)
        self.assertEqual(r[0]["primary_scene_name"], "Grade Beam at Garage")

    def test_metadata_terms(self):
        # word only present in the King Stud footnotes
        self.assertEqual(set(names(dm.search_details("stitched"))), {"(13) ZE STD KING STUD.layout"})

    def test_prefix_matching(self):
        self.assertTrue(dm.search_details("king stu"))

    def test_default_limit_is_80(self):
        self.assertEqual(len(dm.search_details("")), 80)

    def test_source_filter(self):
        src = next(r["layout_file"] for r in dm.search_details("king stud"))
        r = dm.search_details("", source=src)
        self.assertTrue(r)
        self.assertEqual({x["layout_file"] for x in r}, {src})

    def test_punctuation_does_not_crash(self):
        for q in ['(2) A35', '"', 'beam "post', "1/4\" SDS", "AND OR NOT", "*", "@#$%"]:
            with self.subTest(q=q):
                dm.search_details(q)

    def test_drawing_title_and_scene_label(self):
        r = dm.search_details("king stud blw")[0]
        self.assertEqual(r["display_title"], "King Studs at Wall Openings")
        self.assertEqual(r["expanded_title"], "King Studs at Wall Openings")  # not run through abbreviations
        self.assertEqual(r["scene_label"], "King Stud Blw (+1 more view)")
        self.assertTrue(dm.search_details("king studs at wall openings"))

    def test_results_carry_viewports_and_paths(self):
        r = dm.search_details("king stud blw")[0]
        self.assertGreaterEqual(len(r["viewports"]), 1)
        self.assertIsInstance(r["skp_paths_exact"], list)


if __name__ == "__main__":
    unittest.main()
