"""Typo tolerance and load-more paging."""
import unittest

from _support import dm, ensure_indexed, require_fixtures


class TestTypoRules(unittest.TestCase):
    def test_allowed_typos_by_length(self):
        self.assertEqual([dm._allowed_typos(w) for w in ("sj", "tji", "joist", "joists", "hydronics")], [0, 1, 1, 2, 2])

    def test_distance_counts_a_swap_once(self):
        self.assertEqual(dm._typo_distance("hydornics", "hydronics", 2), 1)
        self.assertEqual(dm._typo_distance("joyst", "joist", 1), 1)
        self.assertEqual(dm._typo_distance("abc", "xyz", 1), 2)  # over the limit -> limit + 1


@require_fixtures
class TestTypoSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_indexed()
        dm._VOCAB["words"] = None

    def test_misspelled_word_still_finds(self):
        r = dm.search("stiched")
        self.assertEqual(r["typos"], {"stiched": ["stitched"]})
        self.assertEqual({x["layout_filename"] for x in r["details"]}, {"(13) ZE STD KING STUD.layout"})
        self.assertTrue(dm.search("kingg stud")["details"])

    def test_words_that_match_are_never_changed(self):
        for q in ("TJI", "SJ", "king stu", "hydronic", "stitched"):
            self.assertEqual(dm.search(q)["typos"], {}, q)

    def test_short_words_and_numbers_stay_exact(self):
        self.assertEqual(dm.search("qj")["typos"], {})
        self.assertEqual(dm.search("9PLY")["typos"], {})

    def test_first_letter_must_match(self):
        self.assertNotIn("xtitched", dm.search("xtitched")["typos"])


@require_fixtures
class TestPaging(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_indexed()

    def test_pages_follow_on_without_gaps(self):
        whole = [x["detail_key"] for x in dm.search("", limit=60)["details"]]
        pages = []
        for off in (0, 20, 40):
            r = dm.search("", limit=20, offset=off)
            pages += [x["detail_key"] for x in r["details"]]
        self.assertEqual(pages, whole)
        total = dm.search("")["total"]
        self.assertTrue(dm.search("", limit=20)["has_more"])
        self.assertFalse(dm.search("", limit=20, offset=total - 5)["has_more"])
        self.assertEqual(dm.search("", offset=total)["details"], [])
