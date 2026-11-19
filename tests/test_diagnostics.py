"""Diagnostics log and panel data (backlog D1, D2)."""
import json
import os
import shutil
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import _support
from _support import dm, fixture_files


class TestLogBasics(unittest.TestCase):
    def test_log_lives_in_app_data(self):
        self.assertIsNotNone(dm.LOG_PATH, dm.LOG_SETUP_ERROR)
        self.assertEqual(dm.LOG_PATH, dm.DB.root / "logs" / "detail_manager.log")

    def test_entries_are_single_lines_and_readable(self):
        dm.log_warning("first line\nsecond   line")
        last = dm.read_log_tail(5)[-1]
        self.assertEqual((last["level"], last["message"]), ("WARNING", "first line second line"))

    def test_data_dir_override(self):
        old = os.environ.get(dm.DATA_DIR_ENV)
        try:
            os.environ[dm.DATA_DIR_ENV] = "/some/dev/folder"
            self.assertEqual(dm.app_data_dir(), Path("/some/dev/folder"))
            os.environ[dm.DATA_DIR_ENV] = "  "
            self.assertNotEqual(dm.app_data_dir(), Path("  "))
        finally:
            if old is None: os.environ.pop(dm.DATA_DIR_ENV, None)
            else: os.environ[dm.DATA_DIR_ENV] = old

    def test_logging_failure_does_not_stop_the_program(self):
        blocker = Path(tempfile.mkdtemp()) / "not_a_folder"
        blocker.write_text("x")
        try:
            self.assertIsNone(dm.setup_logging(blocker))  # cannot create <file>/logs
            self.assertTrue(dm.LOG_SETUP_ERROR)
            dm.log_error("goes nowhere, must not raise")
            self.assertEqual(dm.read_log_tail(), [])
        finally:
            dm.setup_logging(dm.DB.root)
        self.assertIsNotNone(dm.LOG_PATH)


class TestIndexDiagnostics(unittest.TestCase):
    def setUp(self):
        self.lib = Path(tempfile.mkdtemp(prefix="dm_test_lib_"))

    def tearDown(self):
        shutil.rmtree(self.lib, ignore_errors=True)
        dm.index_library(str(self.lib)) if self.lib.exists() else None
        _support._INDEXED = False

    def test_broken_master_is_logged_and_listed(self):
        (self.lib / "broken.layout").write_bytes(b"not a zip file")
        dm.index_library(str(self.lib))
        d = dm.diagnostics()
        self.assertIn("broken.layout", [f["layout_filename"] for f in d["failed_masters"]])
        self.assertGreaterEqual(d["problem_count"], 1)
        errors = [x["message"] for x in d["log"] if x["level"] == "ERROR"]
        self.assertTrue(any("broken.layout" in m for m in errors))
        # Nothing but the master itself in the library folder: no logs, no sidecar files.
        self.assertEqual([p.name for p in self.lib.iterdir()], ["broken.layout"])
        (self.lib / "broken.layout").unlink()
        dm.index_library(str(self.lib))
        self.assertEqual(dm.diagnostics()["failed_masters"], [])

    def test_unreachable_library_does_not_wipe_the_index(self):
        if not fixture_files():
            self.skipTest("needs fixtures")
        small = min(fixture_files(), key=lambda p: p.stat().st_size)
        shutil.copy2(small, self.lib / small.name)
        dm.index_library(str(self.lib))
        before = dm.diagnostics()["detail_count"]
        self.assertGreater(before, 0)
        gone = self.lib.with_name(self.lib.name + "_offline")
        self.lib.rename(gone)
        try:
            dm.index_library(str(self.lib))  # must not raise, must not purge
            self.assertIn("Refresh failed", dm.INDEX_STATE["message"])
            self.assertFalse(dm.INDEX_STATE["running"])
            d = dm.diagnostics()
            self.assertEqual(d["detail_count"], before)
            self.assertFalse(d["library_reachable"])
            self.assertTrue(any("Index refresh stopped" in x["message"] for x in d["log"]))
        finally:
            gone.rename(self.lib)

    def test_worker_failures_are_shown(self):
        path = dm.DB.thumbnail_job_root / "last_worker_result.json"
        try:
            path.write_text(json.dumps({"completed_at": "t", "successes": 2, "failures": [{"file": "Z:/a.layout", "error": "boom"}]}))
            w = dm.diagnostics()["worker"]
            self.assertEqual((w["successes"], w["failures"]), (2, [{"file": "Z:/a.layout", "error": "boom"}]))
            path.write_text("{ not json")
            self.assertEqual(len(dm.diagnostics()["worker"]["failures"]), 1)
        finally:
            path.unlink()
        self.assertIsNone(dm.diagnostics()["worker"])


class TestHttp(unittest.TestCase):
    def test_diagnostics_endpoint_and_page(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), dm.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            base = f"http://127.0.0.1:{server.server_address[1]}"
            d = json.loads(urllib.request.urlopen(base + "/api/diagnostics", timeout=10).read())
            for key in ("data_dir", "log_path", "failed_masters", "log", "problem_count", "library_reachable"):
                self.assertIn(key, d)
            page = urllib.request.urlopen(base + "/", timeout=10).read().decode("utf-8")
            for needle in ('id="diagbtn"', 'id="diagback"', "openDiag", "/api/open-log-folder"):
                self.assertIn(needle, page)
            self.assertIn("window.open('/help'", page)
            helppage = urllib.request.urlopen(base + "/help", timeout=10).read().decode("utf-8")
            for needle in ("When to Refresh Index", "Getting a detail into your project", "Open All in LayOut", "Non-Library Details", "thumbnail_worker.rb"):
                self.assertIn(needle, helppage)
        finally:
            server.shutdown(); server.server_close()


if __name__ == "__main__":
    unittest.main()
