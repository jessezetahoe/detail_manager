"""Build a location-independent snapshot of what the parser extracts from a master.

Used by test_golden.py, and by `python tests/make_golden.py` to (re)write the
approved snapshots in tests/golden/. Re-approving is a deliberate act: only do
it when a behavior change (e.g. the 0.2 title fix) is intended, and review the diff.
"""
import hashlib


def snapshot(summary, details):
    out_details = []
    for d in details:
        key_tail = d["detail_key"][len(d["layout_file"]):]  # "|<page_ref>|<viewport>"
        out_details.append({
            "key_tail": key_tail,
            "page_index": d["page_index"],
            "group_index": d["group_index"],
            "page_name": d["page_name"],
            "viewport_count": d["viewport_count"],
            "viewports": [
                {k: v[k] for k in ("viewport_id", "scene_name", "scene_pid", "skp_ref_id", "image_ref_id", "vector_ref_id")}
                | {"has_preview": bool(v["preview_relpath"])}
                for v in d["viewports"]
            ],
            "display_title": d["display_title"],
            "expanded_title": d["expanded_title"],
            "master_title": d["master_title"],
            "skp_paths_exact": d["skp_paths_exact"],
            "bounds": [round(x, 4) for x in d["bounds"]] if d["bounds"] else None,
            "searchable_text_sha1": hashlib.sha1(d["searchable_text"].encode("utf-8")).hexdigest(),
            "raw_text_sha1": hashlib.sha1(d["raw_text"].encode("utf-8")).hexdigest(),
            "raw_lines": len(d["raw_text"].split("\n")) if d["raw_text"] else 0,
            "clean_lines": len(d["clean_text"].split("\n")) if d["clean_text"] else 0,
        })
    return {
        "layout_filename": summary["layout_filename"],
        "page_count": summary["page_count"],
        "detail_count": summary["detail_count"],
        "skp_reference_count": summary["skp_reference_count"],
        "skp_references": {rid: {"externalTarget": r["externalTarget"], "internalTarget": r["internalTarget"]}
                           for rid, r in sorted(summary["skp_references"].items())},
        "details": out_details,
    }
