"""Detail cart (backlog C3): several details sent to LayOut at once, one staging file each."""
import json
import threading
import unittest
import urllib.request
import zipfile
from http.server import ThreadingHTTPServer

from _support import dm, ensure_indexed, require_fixtures


@require_fixtures
class TestCart(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_indexed()
        con = dm.DB.connect()
        cls.keys = [r[0] for r in con.execute("SELECT detail_key FROM details ORDER BY layout_file, page_index, group_index")]
        cls.two_masters = [r[0] for r in con.execute("SELECT MIN(detail_key) FROM details GROUP BY layout_file LIMIT 3")]
        con.close()

    def setUp(self):
        dm.cart_clear()
        self.opened = []
        self._real_open = dm.windows_open
        dm.windows_open = lambda path: self.opened.append(path)

    def tearDown(self):
        dm.windows_open = self._real_open
        dm.cart_clear()

    def test_add_remove_clear_and_persist(self):
        dm.cart_add(self.keys[0]); dm.cart_add(self.keys[1]); dm.cart_add(self.keys[0])  # no double entry
        self.assertEqual([x["detail_key"] for x in dm.cart_contents()["items"]], self.keys[:2])
        saved = json.loads(dm._cart_path().read_text(encoding="utf-8"))["items"]
        self.assertEqual(saved, self.keys[:2])  # survives closing the program
        dm.cart_remove(self.keys[0])
        self.assertEqual([x["detail_key"] for x in dm.cart_contents()["items"]], [self.keys[1]])
        dm.cart_clear()
        self.assertEqual(dm.cart_contents()["items"], [])

    def test_unknown_detail_and_limit(self):
        with self.assertRaises(ValueError):
            dm.cart_add("no such detail")
        for k in self.keys[:dm.CART_LIMIT]:
            dm.cart_add(k)
        with self.assertRaises(ValueError):
            dm.cart_add(self.keys[dm.CART_LIMIT])

    def test_stale_items_are_dropped(self):
        dm._cart_save([self.keys[0], "Z:/gone.layout|id1|id2"])
        c = dm.cart_contents()
        self.assertEqual((len(c["items"]), c["dropped"]), (1, 1))
        self.assertEqual(json.loads(dm._cart_path().read_text(encoding="utf-8"))["items"], [self.keys[0]])

    def test_broken_cart_file_starts_empty(self):
        dm._cart_path().write_text("{ not json", encoding="utf-8")
        self.assertEqual(dm.cart_contents()["items"], [])
        dm.cart_add(self.keys[0])
        self.assertEqual(len(dm.cart_contents()["items"]), 1)

    def test_send_opens_one_staging_file_each_and_empties(self):
        for k in self.two_masters:
            dm.cart_add(k)
        r = dm.cart_send()
        try:
            self.assertEqual((r["opened"], r["failed"]), (len(self.two_masters), []))
            self.assertEqual(len(self.opened), len(self.two_masters))
            for path in self.opened:
                with zipfile.ZipFile(path) as z:
                    self.assertEqual(len([n for n in z.namelist() if n.startswith("pages/") and n.endswith(".xml")]), 1)
            self.assertEqual(dm.cart_contents()["items"], [])
        finally:
            for path in self.opened:
                dm.Path(path).unlink(missing_ok=True)

    def test_failed_detail_stays_in_cart(self):
        real = dm.build_staging
        bad = self.two_masters[0]

        def fake(key):
            if key == bad:
                raise ValueError("simulated failure")
            return real(key)
        dm.build_staging = fake
        try:
            for k in self.two_masters:
                dm.cart_add(k)
            r = dm.cart_send()
            self.assertEqual(r["opened"], len(self.two_masters) - 1)
            self.assertEqual([f["detail_key"] for f in r["failed"]], [bad])
            self.assertEqual([x["detail_key"] for x in dm.cart_contents()["items"]], [bad])
        finally:
            dm.build_staging = real
            for path in self.opened:
                dm.Path(path).unlink(missing_ok=True)

    def test_http_and_page(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), dm.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            base = f"http://127.0.0.1:{server.server_address[1]}"

            def post(path, body=None):
                req = urllib.request.Request(base + path, data=json.dumps(body or {}).encode(), headers={"Content-Type": "application/json"}, method="POST")
                return json.loads(urllib.request.urlopen(req, timeout=10).read())
            self.assertEqual(len(post("/api/cart/add", {"detail_key": self.keys[0]})["items"]), 1)
            c = json.loads(urllib.request.urlopen(base + "/api/cart", timeout=10).read())
            self.assertEqual(c["items"][0]["detail_key"], self.keys[0])
            self.assertTrue(c["items"][0]["thumb"].startswith(("/cache/", "/fullcache/")))
            self.assertEqual(post("/api/cart/clear")["items"], [])
            page = urllib.request.urlopen(base + "/", timeout=10).read().decode("utf-8")
            for needle in ('id="cartbar"', 'id="cartsend"', 'id="cartclear"', "toggleCart", "/api/cart/send"):
                self.assertIn(needle, page)
        finally:
            server.shutdown(); server.server_close()


if __name__ == "__main__":
    unittest.main()
