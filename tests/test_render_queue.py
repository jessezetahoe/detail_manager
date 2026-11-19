"""Render only what is new or changed (backlog P6)."""
import json
import sys
import types
import unittest

import _support
from _support import dm, ensure_indexed, require_fixtures


@require_fixtures
class TestRenderQueue(unittest.TestCase):
    def setUp(self):
        _support._INDEXED = False
        ensure_indexed()
        dm.DB.save_config({"thumbnail_last_queued_layers": None, "thumbnail_hidden_layers": ["GUIDES"]})
        self.queue = dm.DB.thumbnail_job_root / "queue.json"
        con = dm.DB.connect()
        con.execute("UPDATE details SET full_preview_relpath='', render_note=''"); con.commit()  # start with no thumbnails
        self.masters = [r[0] for r in con.execute("SELECT layout_file FROM layout_files WHERE detail_count>0 ORDER BY layout_filename")]
        con.close()

    def tearDown(self):
        _support._INDEXED = False

    def jobs(self):
        return [j["source_layout"] for j in json.loads(self.queue.read_text(encoding="utf-8"))["jobs"]]

    def give_thumbnails(self, files):
        con = dm.DB.connect()
        for f in files:
            con.execute("UPDATE details SET full_preview_relpath='x/y.png' WHERE layout_file=?", (f,))
        con.commit(); con.close()

    def test_only_masters_without_thumbnails(self):
        r = dm.prepare_thumbnail_queue()
        self.assertEqual((r["job_count"], r["already_done"]), (len(self.masters), 0))
        done = self.masters[:3]
        self.give_thumbnails(done)
        r = dm.prepare_thumbnail_queue()
        self.assertEqual(r["job_count"], len(self.masters) - 3)
        self.assertEqual(r["already_done"], 3)
        self.assertFalse(set(done) & set(self.jobs()))
        self.assertEqual(dm.thumbnail_status()["needs_render_count"], len(self.masters) - 3)

    def test_nothing_to_render_removes_old_queue(self):
        dm.prepare_thumbnail_queue()
        self.assertTrue(self.queue.exists())
        self.give_thumbnails(self.masters)
        r = dm.prepare_thumbnail_queue()
        self.assertEqual(r["job_count"], 0)
        self.assertFalse(self.queue.exists(), "an old queue must not be left for the SketchUp step")

    def test_force_and_layer_change_queue_everything(self):
        dm.prepare_thumbnail_queue()
        self.give_thumbnails(self.masters)
        r = dm.prepare_thumbnail_queue(force=True)
        self.assertEqual((r["job_count"], r["everything"]), (len(self.masters), True))
        r = dm.prepare_thumbnail_queue(["GUIDES", "NOTES"])
        self.assertTrue(r["layers_changed"])
        self.assertEqual(r["job_count"], len(self.masters))
        r = dm.prepare_thumbnail_queue(["GUIDES", "NOTES"])
        self.assertEqual(r["job_count"], 0)  # same layers again: nothing new

    def test_off_page_details_do_not_count(self):
        src = self.masters[0]
        self.give_thumbnails(self.masters[1:])
        con = dm.DB.connect()
        con.execute("UPDATE details SET render_note='off_page' WHERE layout_file=?", (src,)); con.commit(); con.close()
        self.assertEqual(dm.thumbnail_status()["needs_render_count"], 0)
        self.assertEqual(dm.prepare_thumbnail_queue()["job_count"], 0)

    def test_processed_masters_are_skipped(self):
        src = self.masters[0]
        self.give_thumbnails([src])
        out = dm.DB.render_root / dm.path_key(src)
        out.mkdir(parents=True, exist_ok=True)
        con = dm.DB.connect(); row = con.execute("SELECT size_bytes, mtime_ns FROM layout_files WHERE layout_file=?", (src,)).fetchone(); con.close()
        manifest = out / "render_manifest.json"
        manifest.write_text(json.dumps({"source_layout": src, "pdf": str(out / "render.pdf"), "expected_size_bytes": row[0], "expected_mtime_ns": row[1], "page_width_inches": 17, "page_height_inches": 11}), encoding="utf-8")
        marker = out / "processed.json"
        marker.write_text(str(manifest.stat().st_mtime_ns), encoding="utf-8")
        had = sys.modules.get("fitz")
        sys.modules["fitz"] = types.ModuleType("fitz")  # never reached for a skipped master
        try:
            r = dm.process_thumbnail_renders()
            self.assertEqual((r["already_done"], r["processed_files"]), (1, 0))
            r = dm.process_thumbnail_renders(force=True)  # forced: tries again (PDF missing -> listed as skipped)
            self.assertEqual(r["already_done"], 0)
            self.assertTrue(any("Rendered PDF missing" in x for x in r["skipped_files"]))
        finally:
            if had is None: sys.modules.pop("fitz", None)
            else: sys.modules["fitz"] = had
            import shutil; shutil.rmtree(out, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
