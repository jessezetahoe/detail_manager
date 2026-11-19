"""Open in SketchUp at the detail's scene (backlog S1)."""
import json
import threading
import time
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from _support import FIXTURES, dm, ensure_indexed, require_fixtures


@require_fixtures
class TestOpenInSketchUp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_indexed()

    def setUp(self):
        self.opened = []
        self._real = dm.windows_open
        dm.windows_open = lambda path: self.opened.append(path)
        self.req = dm.DB.root / dm.SKETCHUP_REQUEST_FILE

    def tearDown(self):
        dm.windows_open = self._real
        self.req.unlink(missing_ok=True)

    def king_stud(self):
        r = [x for x in dm.search_details("king stud blw") if x["layout_filename"].startswith("(13) ZE STD KING STUD")]
        self.assertTrue(r)
        return r[0]

    def test_each_scene_of_a_multi_view_detail(self):
        d = self.king_stud()
        self.assertEqual(len(d["viewports"]), 2)
        for vp in d["viewports"]:
            out = dm.open_in_sketchup(d["detail_key"], vp["viewport_id"])
            req = json.loads(self.req.read_text(encoding="utf-8"))
            self.assertEqual(req["scene_name"], vp["scene_name"])
            self.assertEqual(req["scene_pid"], vp["scene_pid"])
            self.assertEqual(req["skp_path"], out["path"])
            self.assertIn(req["skp_path"], d["skp_paths_exact"])  # exact reference path, never rewritten
            self.assertLess(abs(time.time() - req["created"]), 30)
        self.assertEqual(len(self.opened), 2)

    def test_default_is_the_first_scene(self):
        d = self.king_stud()
        out = dm.open_in_sketchup(d["detail_key"])
        self.assertEqual(out["scene"], d["viewports"][0]["scene_name"])

    def test_nothing_written_next_to_masters(self):
        before = sorted(p.name for p in FIXTURES.iterdir())
        dm.open_in_sketchup(self.king_stud()["detail_key"])
        self.assertEqual(sorted(p.name for p in FIXTURES.iterdir()), before)
        self.assertTrue(str(self.req).startswith(str(dm.DB.root)))

    def test_http(self):
        d = self.king_stud()
        server = ThreadingHTTPServer(("127.0.0.1", 0), dm.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            base = f"http://127.0.0.1:{server.server_address[1]}"
            body = json.dumps({"detail_key": d["detail_key"], "viewport_id": d["viewports"][1]["viewport_id"]}).encode()
            req = urllib.request.Request(base + "/api/open-skp", data=body, headers={"Content-Type": "application/json"}, method="POST")
            j = json.loads(urllib.request.urlopen(req, timeout=10).read())
            self.assertEqual(j["scene"], d["viewports"][1]["scene_name"])
            page = urllib.request.urlopen(base + "/", timeout=10).read().decode("utf-8")
            self.assertIn("data-vp=", page)
            self.assertIn("Open in SketchUp", page)
        finally:
            server.shutdown(); server.server_close()


if __name__ == "__main__":
    unittest.main()
