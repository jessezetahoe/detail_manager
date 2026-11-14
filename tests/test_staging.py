"""Open Detail staging (handoff sections 22, 44, 45).

Default: every multi-viewport detail plus the first and last detail of each master.
Set DM_FULL_STAGING=1 to stage every detail in every fixture.
"""
import os
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from _support import dm, ensure_indexed, require_fixtures

E = dm.NS["e"]


def _props(z):
    root = ET.fromstring(z.read("documentProperties.xml"))
    out = {}
    for el in root.iter():
        n = dm.localname(el.tag)
        if n in ("generator", "version"):
            out[n] = dict(el.attrib)
        if n == "path":
            out["path"] = el.text
    return out


def _skp_refs(z):
    root = ET.fromstring(z.read("references.xml"))
    return {el.get(dm.R_ID): (el.get("externalTarget", ""), el.get("internalTarget", ""))
            for el in root if dm.localname(el.tag) == "skpFileReference"}


def staging_sample():
    con = dm.DB.connect()
    rows = [dict(r) for r in con.execute("SELECT * FROM details ORDER BY layout_file, page_index, group_index")]
    vps = {}
    for r in con.execute("SELECT detail_key, viewport_id FROM viewports"):
        vps.setdefault(r[0], set()).add(r[1])
    con.close()
    if os.environ.get("DM_FULL_STAGING") == "1":
        pick = rows
    else:
        by_file = {}
        for r in rows:
            by_file.setdefault(r["layout_file"], []).append(r)
        pick = []
        for lst in by_file.values():
            chosen = {lst[0]["detail_key"], lst[-1]["detail_key"]} | {r["detail_key"] for r in lst if r["viewport_count"] > 1}
            pick += [r for r in lst if r["detail_key"] in chosen]
    return pick, vps


@require_fixtures
class TestStaging(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_indexed()
        cls.sample, cls.vps = staging_sample()

    def test_sample_covers_multi_viewport(self):
        self.assertTrue(any(r["viewport_count"] > 1 for r in self.sample))

    def test_staging_packages(self):
        for d in self.sample:
            with self.subTest(detail=f"{Path(d['layout_file']).name} p{d['page_index']} g{d['group_index']}"):
                out = dm.build_staging(d["detail_key"])  # raises if validate_staging_package fails
                try:
                    self.assertTrue(str(out).startswith(str(dm.DB.staging_root)))
                    with zipfile.ZipFile(d["layout_file"]) as src, zipfile.ZipFile(out) as stg:
                        names = stg.namelist()
                        pages = [n for n in names if n.startswith("pages/") and n.endswith(".xml")]
                        self.assertEqual(pages, [d["page_xml"]])

                        # exactly one top-level group, containing every viewport of the detail
                        page = ET.fromstring(stg.read(d["page_xml"]))
                        top = list(page.find("p:layerEntityManager/p:entityList", dm.NS))
                        self.assertEqual(len(top), 1)
                        self.assertEqual(dm.localname(top[0].tag), "group")
                        got = {m.get("id") for m in top[0].iter(f"{{{E}}}skpModelRef")}
                        self.assertEqual(got, self.vps[d["detail_key"]])

                        # text/callouts retained: same rtf text count as the master group
                        spage = ET.fromstring(src.read(d["page_xml"]))
                        sgroups = [x for x in spage.find("p:layerEntityManager/p:entityList", dm.NS) if dm.localname(x.tag) == "group"]
                        sg = next(g for g in sgroups if d["primary_viewport_id"] in {m.get("id") for m in g.iter(f"{{{E}}}skpModelRef")})
                        self.assertEqual(dm.text_from_group(top[0]), dm.text_from_group(sg))

                        # exact external SKP paths and identical embedded SKP payloads
                        src_refs, stg_refs = _skp_refs(src), _skp_refs(stg)
                        self.assertTrue(stg_refs)
                        for rid, (ext, internal) in stg_refs.items():
                            self.assertEqual((ext, internal), src_refs[rid])
                            if internal:
                                a, b = src.getinfo(internal), stg.getinfo(internal)
                                self.assertEqual((a.CRC, a.file_size), (b.CRC, b.file_size), "embedded SKP changed")

                        # original LayOut version metadata and document path preserved
                        self.assertEqual(_props(stg), _props(src))
                        self.assertLess(out.stat().st_size, Path(d["layout_file"]).stat().st_size)
                finally:
                    out.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
