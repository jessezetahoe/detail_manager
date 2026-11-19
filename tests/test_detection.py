"""Detail-detection rules from the handoff (sections 4, 5, 14)."""
import unittest
import xml.etree.ElementTree as ET
import zipfile

from _support import FIXTURES, dm, fixture_files, parse, require_fixtures

E_GROUP = f"{{{dm.NS['e']}}}group"
E_SKP = f"{{{dm.NS['e']}}}skpModelRef"


def raw_external_targets(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("references.xml"))
    return {el.get(dm.R_ID): el.get("externalTarget", "") for el in root if dm.localname(el.tag) == "skpFileReference"}


@require_fixtures
class TestDetection(unittest.TestCase):
    def test_every_viewport_in_a_top_level_group_is_in_exactly_one_detail(self):
        for p in fixture_files():
            with self.subTest(master=p.name):
                summary, details = parse(p)
                found = [v["viewport_id"] for d in details for v in d["viewports"]]
                self.assertEqual(len(found), len(set(found)), "viewport counted twice")
                expected, loose = [], 0
                with zipfile.ZipFile(p) as z:
                    doc = ET.fromstring(z.read("document.xml"))
                    refs = {el.get(dm.R_ID): el.get("internalTarget") for el in ET.fromstring(z.read("references.xml"))}
                    for pr in doc.findall(".//ld:pageRef", dm.NS):
                        page = ET.fromstring(z.read(refs[pr.get(dm.R_ID)]))
                        top = page.find("p:layerEntityManager/p:entityList", dm.NS)
                        for ent in list(top):
                            ids = [m.get("id") for m in ent.iter(E_SKP)]
                            if ent.tag == E_GROUP:
                                expected += ids
                            else:
                                loose += len(ids)
                self.assertEqual(sorted(found), sorted(expected))
                # Handoff 14: no loose viewports outside top-level groups in tested masters.
                self.assertEqual(loose, 0, "loose SketchUp viewport outside a detail group - review the grouping rule")

    def test_multi_viewport_details_stay_one_detail(self):
        cases = {
            "(13) ZE STD KING STUD.layout": [2, 2],
            "(13) ZE STD PERF WALL.layout": [4, 4],
        }
        for name, counts in cases.items():
            p = FIXTURES / name
            if not p.exists():
                continue
            with self.subTest(master=name):
                _, details = parse(p)
                self.assertEqual([d["viewport_count"] for d in details], counts)
        p = FIXTURES / "(13) ZE STD KING STUD.layout"
        if p.exists():
            _, details = parse(p)
            self.assertEqual([v["scene_name"] for v in details[0]["viewports"]], ["King Stud Blw", "King Stud Abv"])

    def test_skp_paths_are_exact_external_targets(self):
        for p in fixture_files():
            with self.subTest(master=p.name):
                raw = raw_external_targets(p)
                summary, details = parse(p)
                for d in details:
                    for v in d["viewports"]:
                        self.assertIn(raw[v["skp_ref_id"]], d["skp_paths_exact"])
                    for path in d["skp_paths_exact"]:
                        self.assertIn(path, raw.values())  # character-for-character, no normalizing

    def test_library_has_nothing_off_the_sheet(self):
        for p in fixture_files():
            self.assertEqual(parse(p)[0]["off_sheet_details"], 0, p.name)

    def test_detail_key_format(self):
        for p in fixture_files():
            _, details = parse(p)
            for d in details:
                self.assertEqual(d["detail_key"], f"{p}|{d['page_ref_id']}|{d['primary_viewport_id']}")


if __name__ == "__main__":
    unittest.main()
