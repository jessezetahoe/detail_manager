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

    def test_tokens_starting_with_a_digit(self):
        self.assertEqual(dm.expand_abbreviations("FLR TO 3PLY BEAM"), "Floor TO Triple Ply Beam")
        self.assertEqual(dm.expand_abbreviations("2PLY"), "Double Ply")
        self.assertEqual(dm.expand_abbreviations("2X6 Pe2Pe 4PLY"), "2X6 Pe2Pe 4PLY")  # unlisted stays

    def test_case_insensitive_lookup(self):
        self.assertEqual(dm.expand_abbreviations("flr"), "Floor")

    def test_whitespace_collapsed(self):
        self.assertEqual(dm.expand_abbreviations("  FLR   TO  FND "), "Floor TO Foundation")

    def test_no_words_that_are_not_in_the_detail(self):
        # An expansion must not add search words the detail does not have:
        # "TRAD" once added "(No Hydronics)", so searching hydronics found traditional details.
        for k, v in dm.ABBREVIATIONS.items():
            self.assertNotRegex(v, r"\(|e\.g\.", f"{k}: {v}")
        self.assertNotIn("Hydronics", dm.ABBREVIATIONS["TRAD"])

    def test_abbreviations_are_part_of_the_read_rules_key(self):
        self.assertTrue(dm.READ_RULES_KEY.startswith(f"{dm.INDEX_VERSION}:"))

    def test_master_title_strips_numeric_prefix(self):
        self.assertEqual(dm.master_intended_title("(13) ZE STD KING STUD"), "ZE Standard KING STUD")
        self.assertEqual(dm.master_intended_title("(03) FLR TO FLR TRAD EXT SJ WSW (New Details!)"),
                         "Floor TO Floor Traditional Framing Exterior Solid Joist Wood Strong Wall (New Details!)")


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


class TestCleanText(unittest.TestCase):
    def test_noise_is_dropped(self):
        for junk in ("1", "10", "100", " 7 ", "N.T.S.", "NTS", "not to scale", "XXX", "xxx", "", "  "):
            self.assertTrue(dm.is_noise_text(junk), repr(junk))

    def test_real_content_is_kept(self):
        for keep in ("2X6 STUD", "(2) A35", '2 1/4"', "1/4", '4"', "1 3/4", "16d NAILS", "HDU2", "TYP", "plan",
                     "\u2264 4'-0\"", "2018 IRC KING STUD REQUIREMENTS", "BEAM POCKET PER\nDTL XXX", "1234", "1.5\""):
            self.assertFalse(dm.is_noise_text(keep), repr(keep))

    def test_order_kept_and_input_untouched(self):
        raw = ["6", "King Studs at Wall Openings", "N.T.S.", "XXX", "1", "2X STUD WALL PER PLAN, TYP"]
        copy = list(raw)
        self.assertEqual(dm.clean_text_blocks(raw), ["King Studs at Wall Openings", "2X STUD WALL PER PLAN, TYP"])
        self.assertEqual(raw, copy)


class TestInferTitle(unittest.TestCase):
    def test_title_in_text_box_before_nts(self):
        # How the library is drawn: title box, then a separate N.T.S. box.
        texts = ["6", "5", "King Studs at Wall Openings", "N.T.S.", "XXX", "2X STUD WALL PER PLAN, TYP"]
        self.assertEqual(dm.infer_title_with_source(texts, ["King Stud Blw"], "Pg"), ("King Studs at Wall Openings", "drawing"))

    def test_title_above_nts_in_same_block(self):
        self.assertEqual(dm.infer_title(["Joist Connection @ Wood Beam\nN.T.S."], ["Scene"], "Pg"), "Joist Connection @ Wood Beam")

    def test_nts_spellings(self):
        for nts in ("N.T.S.", "NTS", "n.t.s", "NOT TO SCALE"):
            self.assertEqual(dm.infer_title(["Step Footing", nts], ["S"], "P"), "Step Footing", nts)

    def test_bubble_or_placeholder_before_nts_is_not_a_title(self):
        for junk in ("7", "XXX", "N.T.S."):
            self.assertEqual(dm.infer_title_with_source([junk, "N.T.S."], ["Scene A"], "Pg"), ("Scene A", "scene"), junk)

    def test_title_after_nts_when_none_before(self):
        # Job files sometimes have the title box after N.T.S.
        self.assertEqual(dm.infer_title_with_source(["N.T.S.", "Something"], ["Scene A"], "Pg"), ("Something", "drawing"))

    def test_falls_back_to_page_name(self):
        self.assertEqual(dm.infer_title_with_source([], [], "Page 3"), ("Page 3", "page"))
        self.assertEqual(dm.infer_title([], [], ""), "Untitled Detail")

    def test_prototype_rule_kept_for_comparison(self):
        self.assertEqual(dm._infer_title_poc07a(["King Studs at Wall Openings", "N.T.S."], ["King Stud Blw"], "Pg"), "King Stud Blw")


if __name__ == "__main__":
    unittest.main()
