"""Search chips / Filters panel (backlog A2)."""
import json
import re
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from _support import dm, ensure_indexed, require_fixtures


def ids(chips):
    return set(chips)


class TestChipRules(unittest.TestCase):
    def test_shipped_file_matches_built_in_list(self):
        raw = json.loads(dm.chips_path().read_text(encoding="utf-8"))
        a, b = dm._validate_chips(raw), dm._validate_chips(dm.DEFAULT_CHIP_GROUPS)
        self.assertEqual([(g["name"], g["exclusive"], [(c["id"], c["file"], c["scene"]) for c in g["chips"]]) for g in a],
                         [(g["name"], g["exclusive"], [(c["id"], c["file"], c["scene"]) for c in g["chips"]]) for g in b])

    def test_file_name_decides_either_or_groups(self):
        # Real case: a Solid Joist master whose scenes say "TJI".
        c = dm.compute_chips("(03) FLR TO FLR TRAD EXT SJ WSW (New Details!).layout", ["TJI Para NW ABV WSW"])
        self.assertIn("joist:solid-joist", c)
        self.assertNotIn("joist:i-joist", c)
        for want in ("floor-system:traditional", "location:exterior", "wall:no-wall-above", "other:strong-wall", "joist-direction:parallel"):
            self.assertIn(want, c)
        self.assertNotIn("wall:wall-above", c)   # "NW ABV" means no wall above
        self.assertNotIn("wall:no-wall", c)

    def test_wall_phrases(self):
        # Real patterns from the library scan (2026-11-22).
        w = lambda scene: sorted(c.split(":")[1] for c in dm.compute_chips("x.layout", [scene]) if c.startswith("wall:"))
        self.assertEqual(w("Pa 2 Ply Bm Wall Abv Hyd"), ["no-wall-below", "wall-above"])
        self.assertEqual(w("Pa 2 Ply Bm Wall Abv Blw Shear Hyd"), ["wall-above", "wall-below"])
        self.assertEqual(w("Pa2Pa 2 Ply Bm Wall Abv SJ Roof Abv Shear Hyd"), ["no-wall-below", "wall-above"])  # Roof Abv is not a wall
        self.assertEqual(w("Pa 2 Ply Bm Wall Blw Hyd"), ["no-wall-above", "wall-below"])
        self.assertEqual(w("TJI Para NW ABV Hyd"), ["no-wall-above"])
        self.assertEqual(w("TJI Pa2Pe nw blw"), ["no-wall-below"])
        self.assertEqual(w("Pa Top Cont NW Hyd"), ["no-wall"])
        self.assertEqual(w("TJI Pa Cont Hyd No Wall"), ["no-wall"])
        for unrelated in ("Grade Beam Blw Frame", "HD Abv & Blw 2 Ply Bm", "Pe2Pa Abv", "Stem Conc. w/ Wall Int Slab"):
            self.assertEqual(w(unrelated), [], unrelated)
        self.assertIn("other:roof-outside", dm.compute_chips("x.layout", ["Wall Abv SJ Roof Abv"]))
        # each word counts once, longest code first
        self.assertEqual(dm._codes_found(["WALL", "ABV", "BLW"], {("WALL", "ABV"), ("WALL", "ABV", "BLW")}), {("WALL", "ABV", "BLW")})

    def test_scene_names_when_the_file_name_says_nothing(self):
        c = dm.compute_chips("1757 S0.1.layout", ["TJI Pa2Pe Hyd Wall Blw"])
        for want in ("joist:i-joist", "floor-system:hydronics", "joist-direction:para-perp", "wall:wall-below"):
            self.assertIn(want, c)

    def test_whole_words_and_capitals(self):
        c = dm.compute_chips("x.layout", ["pa2pa hang"])
        self.assertIn("joist-direction:para-para", c)
        self.assertNotIn("joist-direction:parallel", c)  # "Pa2Pa" is one word, not "Pa"
        self.assertEqual(dm.compute_chips("(04) FLR TO STL BEAM HYD.layout", []) & {"beam:steel", "floor-system:hydronics"}, {"beam:steel", "floor-system:hydronics"})

    def test_notes_are_never_used(self):
        self.assertEqual(dm.compute_chips("plain.layout", []), set())

    def test_broken_file_falls_back(self):
        real = dm.chips_path
        tmp = Path(tempfile.mkdtemp()) / "chips.json"
        try:
            dm.chips_path = lambda: tmp
            for bad in ("{ nope", '{"groups": []}', '{"groups": [{"name": "X", "chips": [{"label": "Y"}]}]}'):
                with self.subTest(bad=bad):
                    tmp.write_text(bad, encoding="utf-8"); dm._CHIP_CFG_CACHE["groups"] = None
                    self.assertEqual(len(dm.chips_config()), len(dm.DEFAULT_CHIP_GROUPS))
                    self.assertTrue(dm._CHIP_CFG_CACHE["error"])
            self.assertIn("chips.json could not be used", dm.read_log_tail(5)[-1]["message"])
        finally:
            dm.chips_path = real; dm._CHIP_CFG_CACHE["groups"] = None


@require_fixtures
class TestChipSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_indexed()

    def scenes(self, d):
        return {t.upper() for v in d["viewports"] for t in re.findall(r"[A-Za-z0-9]+", v["scene_name"] or "")}

    def test_counts_and_total(self):
        r = dm.search("", limit=500)
        self.assertEqual(r["total"], len(r["details"]))
        self.assertTrue(r["chip_counts"])
        for cid, n in r["chip_counts"].items():
            self.assertLessEqual(n, r["total"], cid)

    def test_must_have(self):
        r = dm.search("", limit=500, chips_on=["foundation:retaining"])
        self.assertTrue(r["details"])
        self.assertEqual(r["total"], dm.search("", limit=500)["chip_counts"]["foundation:retaining"])
        for d in r["details"]:
            self.assertTrue("RET" in d["layout_filename"].upper().split() or "RET" in self.scenes(d))

    def test_must_not_have_and_combined(self):
        allr = dm.search("", limit=500)
        r = dm.search("", limit=500, chips_off=["floor-system:hydronics"])
        self.assertEqual(r["total"], allr["total"] - allr["chip_counts"].get("floor-system:hydronics", 0))
        self.assertFalse([d for d in r["details"] if "HYD" in d["layout_filename"].upper().split()])
        both = dm.search("footing", limit=500, chips_on=["foundation:retaining"], chips_off=["floor-system:hydronics"])
        self.assertLessEqual(both["total"], r["total"])

    def test_search_details_still_returns_a_list(self):
        self.assertIsInstance(dm.search_details("king"), list)

    def test_http_and_page(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), dm.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            base = f"http://127.0.0.1:{server.server_address[1]}"
            r = json.loads(urllib.request.urlopen(base + "/api/search?q=&on=foundation:retaining&off=", timeout=10).read())
            self.assertIn("chip_counts", r); self.assertIn("total", r)
            st = json.loads(urllib.request.urlopen(base + "/api/status", timeout=10).read())
            self.assertEqual(len(st["chips"]), len(dm.chips_config()))
            page = urllib.request.urlopen(base + "/", timeout=10).read().decode("utf-8")
            for needle in ('id="filtersbtn"', 'id="filterpanel"', "renderChips", "&on="):
                self.assertIn(needle, page)
        finally:
            server.shutdown(); server.server_close()


if __name__ == "__main__":
    unittest.main()
