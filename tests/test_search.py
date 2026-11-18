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

    def test_hydronics_does_not_find_traditional_details(self):
        hits = {r["layout_filename"] for r in dm.search_details("hydronics")}
        self.assertTrue(hits)
        self.assertFalse([h for h in hits if "TRAD" in h], hits)

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

    def test_raw_clean_and_notes_text(self):
        r = dm.search_details("king stud blw")[0]
        raw, clean, notes = r["raw_text"].split("\n"), r["clean_text"].split("\n"), r["notes_text"].split("\n")
        self.assertIn("N.T.S.", raw); self.assertIn("XXX", raw); self.assertIn("6", raw)
        self.assertFalse([x for x in clean if x.strip().isdigit() and len(x.strip()) <= 3])
        self.assertNotIn("N.T.S.", clean); self.assertNotIn("XXX", clean)
        self.assertIn("King Studs at Wall Openings", clean)
        self.assertNotIn("King Studs at Wall Openings", notes)  # the title is not repeated in the notes
        self.assertIn("2X STUD WALL PER PLAN, TYP", notes)
        self.assertIn('1/4" SDS SCREWS', notes)

    def test_placeholder_only_matches_inside_real_notes(self):
        # "XXX" alone (the detail-number placeholder) is gone; "PER DTL XXX" in a note still counts.
        hits = dm.search_details("XXX")
        self.assertLess(len(hits), 80)
        for r in hits:
            self.assertNotIn("XXX", r["clean_text"].split("\n"))
            self.assertIn("xxx", r["clean_text"].lower())
        self.assertTrue(dm.search_details("A35"))

    def test_results_carry_viewports_and_paths(self):
        r = dm.search_details("king stud blw")[0]
        self.assertGreaterEqual(len(r["viewports"]), 1)
        self.assertIsInstance(r["skp_paths_exact"], list)


if __name__ == "__main__":
    unittest.main()
