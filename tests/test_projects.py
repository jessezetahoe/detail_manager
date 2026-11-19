"""Old Projects: job LayOut files as a second, separate source (backlog O1 to O4).

Uses the job files in tests/fixtures/projects (local only, not in git).
"""
import re
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import _support
from _support import FIXTURES, ROOT, dm, parse

PROJECTS = ROOT / "tests" / "fixtures" / "projects"


def project_files():
    return sorted(PROJECTS.glob("*.layout")) if PROJECTS.is_dir() else []


def require_projects(test):
    return unittest.skipUnless(project_files() and list(FIXTURES.glob("*.layout")), "needs tests/fixtures/projects and company fixtures")(test)


class TestJobNames(unittest.TestCase):
    def test_job_number(self):
        self.assertEqual(dm.job_number("1757 S0.1.layout"), "1757")
        self.assertEqual(dm.job_number("1875 S2.1-S2.4.layout"), "1875")
        self.assertEqual(dm.job_number("(03) FLR TO FLR.layout"), "")
        self.assertEqual(dm.job_number("12 short.layout"), "")

    def test_sheet_label(self):
        self.assertEqual(dm.sheet_label({"page_name": "S2.6", "layout_filename": "1875 S2.5-S2.8.layout"}), "S2.6")
        self.assertEqual(dm.sheet_label({"page_name": "", "layout_filename": "1757 S0.1.layout"}), "S0.1")

    def test_default_scene_names(self):
        for n in ("Scene 3", "scene", "Page 2", "Last saved SketchUp View", "", "  "):
            self.assertTrue(dm.is_default_scene(n), n)
        for n in ("King Stud Blw", "Floor to Floor", "Scene at Garage"):
            self.assertFalse(dm.is_default_scene(n), n)

    def test_title_after_nts_and_fallbacks(self):
        t = dm.infer_title_with_source
        self.assertEqual(t(["N.T.S.", "Shear Transfer @ Depressed Shower", "801"], ["Last saved SketchUp View"], ""), ("Shear Transfer @ Depressed Shower", "drawing"))
        self.assertEqual(t(["Title Before", "N.T.S.", "Title After"], [], ""), ("Title Before", "drawing"))  # library order wins
        self.assertEqual(t(["<>", "EQ", "SIDE VIEW"], ["Scene 3"], "S2.5"), ("SIDE VIEW", "text"))
        self.assertEqual(t(["<>", "1/4"], ["Scene 3"], "S2.5"), ("S2.5", "page"))

    def test_model_tags(self):
        cfg = dm.DB.get_config()
        dm.DB.save_config({"library_root": "Z:/Google Drive/ZE Library/ZE Scrapbooks"})
        try:
            self.assertEqual(dm.model_tags(["Z:/Google Drive/ZE Library/ZE Scrapbooks/_Models/(02) FLR TO FND/x.skp"]), ["Library model"])
            self.assertEqual(dm.model_tags(["Z:\\Google Drive\\ZE Sketchup\\ZE Detail Scrapbooks\\Details\\_Models\\a.skp"]), ["Old library model"])
            self.assertEqual(dm.model_tags(["Z:/Google Drive/ZE Sketchup/ZE Custom Job Details/1875/a.skp", ""]), ["Custom model"])
        finally:
            dm.DB.save_config({"library_root": cfg.get("library_root", "")})


@require_projects
class TestProjectFiles(unittest.TestCase):
    def test_detection_on_job_files(self):
        total = skipped = drawn = 0
        for p in project_files():
            with self.subTest(file=p.name):
                summary, details = parse(p)
                self.assertGreater(len(details), 0)
                ids = [v["viewport_id"] for d in details for v in d["viewports"]]
                self.assertEqual(len(ids), len(set(ids)))
                total += len(details); skipped += summary["skipped_viewports"]
                for d in details:
                    self.assertFalse(dm.is_default_scene(d["display_title"]), d["display_title"])
                    if d["display_title"] not in [v["scene_name"] for v in d["viewports"]]:
                        drawn += 1
        self.assertGreater(total, 0)
        self.assertGreaterEqual(drawn / total, 0.95, f"{drawn}/{total} details with a drawn title")

    def test_known_title_after_nts(self):
        p = PROJECTS / "1757 S0.8.layout"
        if not p.exists():
            self.skipTest("sample not present")
        titles = [d["display_title"] for d in parse(p)[1]]
        self.assertIn("Shear Transfer @ Depressed Shower Parallel", titles)


@require_projects
class TestTwoSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dm.index_library(str(FIXTURES), str(PROJECTS))
        cls.state = dict(dm.INDEX_STATE)

    @classmethod
    def tearDownClass(cls):
        empty = Path(tempfile.mkdtemp(prefix="dm_test_noproj_"))
        dm.index_library(str(FIXTURES), str(empty))  # removes the Old Projects entries again
        shutil.rmtree(empty, ignore_errors=True)
        _support._INDEXED = False

    def test_refresh_reads_both(self):
        self.assertEqual(self.state["errors"], [])
        self.assertIn("Old Projects:", self.state["message"])

    def test_sources_stay_separate(self):
        lib = dm.search_details("")
        self.assertTrue(lib)
        self.assertEqual({r["source_kind"] for r in lib}, {"library"})
        proj = dm.search_details("", src="projects")
        self.assertTrue(proj)
        self.assertEqual({r["source_kind"] for r in proj}, {"projects"})
        for r in proj:
            self.assertTrue(r["job_number"])
            self.assertIn("model_tags", r)

    def test_both_ranks_library_first_for_equal_matches(self):
        r = dm.search_details("continuous footing", src="both", limit=200)
        kinds = [x["source_kind"] for x in r]
        self.assertIn("library", kinds); self.assertIn("projects", kinds)
        self.assertEqual(kinds[0], "library")

    def test_jobs_and_categories(self):
        jobs = {j["job"]: j for j in dm.library_jobs()}
        expected = {dm.job_number(p.name) for p in project_files()}
        self.assertEqual(set(jobs), expected)
        self.assertEqual([j["job"] for j in dm.library_jobs()], sorted(expected, key=int, reverse=True))
        cats = {g["name"] for g in dm.library_categories()}
        self.assertNotIn("Other", cats)  # job files never land in the library categories
        some_job = next(iter(expected))
        r = dm.search_details("", src="projects", job=some_job, limit=500)
        self.assertTrue(r)
        self.assertEqual({x["job_number"] for x in r}, {some_job})
        self.assertEqual(dm.search_details("", category="Foundation", src="projects"), [])

    def test_skipped_viewports_in_diagnostics(self):
        d = dm.diagnostics()
        self.assertEqual(d["project_file_count"], len(project_files()))
        total_skipped = sum(parse(p)[0]["skipped_viewports"] for p in project_files())
        self.assertEqual(sum(f["skipped_viewports"] for f in d["skipped_viewports"]), total_skipped)

    def test_library_match_is_exact_model_and_scene(self):
        r = dm.search_details("", src="projects", limit=2000)
        for x in r:
            m = x["library_match"]
            if m:
                self.assertIn("Library model", x["model_tags"])
                con = dm.DB.connect()
                row = con.execute("SELECT 1 FROM details d JOIN layout_files lf ON lf.layout_file=d.layout_file WHERE d.detail_key=? AND COALESCE(lf.source_kind,'library')='library'", (m["detail_key"],)).fetchone()
                con.close()
                self.assertTrue(row)

    def test_open_detail_from_a_job_file(self):
        smallest = min(project_files(), key=lambda p: p.stat().st_size)
        con = dm.DB.connect()
        row = con.execute("SELECT detail_key, viewport_count FROM details WHERE layout_file=? ORDER BY viewport_count DESC LIMIT 1", (str(smallest),)).fetchone()
        con.close()
        out = dm.build_staging(row[0])
        try:
            with zipfile.ZipFile(out) as z:
                pages = [n for n in z.namelist() if n.startswith("pages/") and n.endswith(".xml")]
                self.assertEqual(len(pages), 1)
        finally:
            out.unlink(missing_ok=True)

    def test_unreachable_projects_folder_keeps_library_and_old_projects(self):
        before = dm.diagnostics()
        gone = str(PROJECTS) + "_not_there"
        dm.index_library(str(FIXTURES), gone)
        s = dict(dm.INDEX_STATE)
        self.assertIn("NOT reachable", s["message"])
        after = dm.diagnostics()
        self.assertEqual((after["detail_count"], after["project_file_count"]), (before["detail_count"], before["project_file_count"]))
        self.assertTrue(any("Old Projects skipped" in x["message"] for x in after["log"]))


if __name__ == "__main__":
    unittest.main()
