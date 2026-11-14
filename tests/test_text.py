"""Pure-text behavior: RTF extraction, abbreviations, titles."""
import unittest

from _support import dm


class TestAbbreviations(unittest.TestCase):
    def test_external_json_is_loaded(self):
        self.assertTrue(dm.abbreviations_path().exists())
        self.assertEqual(dm.ABBREVIATIONS.get("TJI"), "I-Joist")

    def test_tji_expands_to_i_joist(self):
        self.assertEqual(dm.expand_abbreviations("TJI Para WSW"), "I-Joist Parallel Wood Strong Wall")

    def test_exact_tokens_only(self):
        # Unknown shorthand and partial matches stay untouched.
        self.assertEqual(dm.expand_abbreviations("Pe2Pe Wd Bm"), "Pe2Pe Wd Bm")
        self.assertEqual(dm.expand_abbreviations("FLRS"), "FLRS")

    def test_case_insensitive_lookup(self):
        self.assertEqual(dm.expand_abbreviations("flr"), "Floor")

    def test_whitespace_collapsed(self):
        self.assertEqual(dm.expand_abbreviations("  FLR   TO  FND "), "Floor TO Foundation")

    def test_master_title_strips_numeric_prefix(self):
        self.assertEqual(dm.master_intended_title("(13) ZE STD KING STUD"), "ZE Standard KING STUD")
        self.assertEqual(dm.master_intended_title("(03) FLR TO FLR TRAD EXT SJ WSW (New Details!)"),
                         "Floor TO Floor Traditional Framing (No Hydronics) Exterior Solid Joist Wood Strong Wall (New Details!)")


class TestRtf(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(dm.rtf_to_text(r"{\rtf1\ansi {\fonttbl\f0 Arial;}\f0 2X6 STUD}"), "2X6 STUD")

    def test_paragraphs_become_lines(self):
        self.assertEqual(dm.rtf_to_text(r"{\rtf1 LINE ONE\par LINE TWO}"), "LINE ONE\nLINE TWO")

    def test_hex_and_unicode_escapes(self):
        self.assertEqual(dm.rtf_to_text(r"{\rtf1 4\'27-0\'22}"), "4'-0\"")
        self.assertEqual(dm.rtf_to_text("{\\rtf1\\uc1 " + "\\" + "u8804?4}"), "\u2264" + "4")

    def test_destinations_skipped(self):
        self.assertEqual(dm.rtf_to_text(r"{\rtf1{\colortbl;\red0\green0\blue0;}{\*\generator Foo;}TEXT}"), "TEXT")

    def test_empty(self):
        self.assertEqual(dm.rtf_to_text(""), "")


class TestInferTitle(unittest.TestCase):
    """Documents CURRENT behavior (baseline). Update deliberately with the title fix."""

    def test_title_above_nts_in_same_block(self):
        self.assertEqual(dm.infer_title(["Joist Connection @ Wood Beam\nN.T.S."], ["Scene"], "Pg"),
                         "Joist Connection @ Wood Beam")

    def test_baseline_misses_title_in_separate_block(self):
        # Real masters keep the title and N.T.S. in separate text boxes;
        # the baseline falls back to the scene name. Known issue for 0.2.
        self.assertEqual(dm.infer_title(["King Studs at Wall Openings", "N.T.S."], ["King Stud Blw"], "Pg"),
                         "King Stud Blw")

    def test_falls_back_to_page_name(self):
        self.assertEqual(dm.infer_title([], [], "Page 3"), "Page 3")
        self.assertEqual(dm.infer_title([], [], ""), "Untitled Detail")


if __name__ == "__main__":
    unittest.main()
