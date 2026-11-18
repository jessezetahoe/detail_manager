#!/usr/bin/env python3
"""
Detail Manager Prototype 0.1
Local browser GUI for a LayOut detail library.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import logging
import mimetypes
import os
import re
import shutil
import sqlite3
import sys
import threading
import time
import urllib.parse
import webbrowser
import zipfile
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
import xml.etree.ElementTree as ET
from xml.dom import minidom, Node

APP_NAME = "ZE Detail Manager Prototype 0.1"
APP_DIR_NAME = "ZE Detail Manager Prototype 0.1"
PORT_DEFAULT = 8768
# Raise this whenever the rules for reading a master change (titles, text...).
# Masters indexed under an older number are re-read on the next refresh even
# though the file itself has not changed; their thumbnails are kept.
INDEX_VERSION = 3

NS = {
    "e": "http://sketchup.google.com/schemas/layout/1.0/entities",
    "ld": "http://sketchup.google.com/schemas/layout/1.0/layoutdocument",
    "p": "http://sketchup.google.com/schemas/layout/1.0/page",
    "r": "http://sketchup.google.com/schemas/layout/1.0/references",
    "l": "http://sketchup.google.com/schemas/layout/1.0/layout",
}
for prefix, uri in NS.items():
    with contextlib.suppress(Exception):
        ET.register_namespace(prefix, uri)
R_ID = f"{{{NS['r']}}}id"
L_REF = f"{{{NS['l']}}}ref"

DESTINATIONS = {
    "fonttbl", "colortbl", "datastore", "themedata", "stylesheet", "info",
    "pict", "object", "listtable", "listoverridetable", "rsidtbl", "generator",
    "xmlnstbl", "filetbl", "revtbl", "latentstyles", "colorschememapping",
}


DEFAULT_ABBREVIATIONS = {
    "2PLY": "Double Ply",
    "3PLY": "Triple Ply",
    "ALT": "Alternative or Optional",
    "BEAM": "Beam",
    "BEAR": "Bearing",
    "BOLT": "Bolted",
    "CAL": "California Fill",
    "CB": "Column Base",
    "CBTZ": "CBTZ",
    "CHIM": "Chimney",
    "CMBO": "Combination",
    "CNCL": "Concealed",
    "CONN": "Connection",
    "CRNR": "Corner",
    "CVTY": "Cavity",
    "DBL": "Double Detail",
    "DECK": "Decking",
    "DRAN": "Drain",
    "EXT": "Exterior",
    "FILL": "Fill",
    "FILR": "Filler",
    "FLAT": "Flat Rafter / Joist",
    "FLR": "Floor",
    "FLSH": "Flush",
    "FND": "Foundation",
    "FRME": "Frame",
    "GBLE": "Gable",
    "GRDR": "Girder Truss",
    "GRGE": "Garage",
    "GRAD": "Grade",
    "HD": "Holdown",
    "HEDR": "Header",
    "HYD": "Hydronics",
    "ICE": "Ice Splitter",
    "INSL": "Insulation",
    "INT": "Interior",
    "ISO": "Isolated",
    "KP": "Knife Plate",
    "NAIL": "Nailing",
    "NALR": "Nailer",
    "NW": "No Wall",
    "OFH": "Offset Heights",
    "OVER": "Overframing",
    "PACK": "Dry Pack",
    "PARA": "Parallel",
    "PED": "Pedestal",
    "PERF": "Perforated Wall",
    "PERP": "Perpendicular",
    "PKT": "Pocket",
    "PKOT": "Packout",
    "POST": "Post or Column",
    "RET": "Retaining Wall",
    "SDS": "SDS Screws",
    "SHR": "Shear",
    "SJ": "Solid Joist",
    "SLEP": "Sleeper System",
    "SLPD": "Sloped",
    "SOLD": "Solid",
    "SPLC": "Spliced Connection",
    "STD": "Standard",
    "STL": "Steel",
    "STLP": "Steel Post",
    "STRP": "Strap",
    "TAIL": "Truss Tail",
    "TJ": "Truss Joist",
    "TJI": "I-Joist",
    "TPL": "Triple Detail",
    "TRAD": "Traditional Framing",
    "TRSS": "Truss",
    "TYP": "Typical",
    "WDP": "Wood Post",
    "WELD": "Welded",
    "WSP": "W Section Post",
    "WSW": "Wood Strong Wall",
    "XFR": "Transfer",
}


def abbreviations_path() -> Path:
    return Path(__file__).with_name("abbreviations.json")


def load_abbreviations() -> dict:
    path = abbreviations_path()
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return {str(k).upper(): str(v) for k, v in raw.items()}
        except Exception:
            pass
    return dict(DEFAULT_ABBREVIATIONS)


ABBREVIATIONS = load_abbreviations()
# What a master's index entry depends on besides the file itself. Stored per master;
# when it changes (new reading rules, or abbreviations.json edited), the next
# Refresh Index re-reads unchanged masters once and keeps their thumbnails.
READ_RULES_KEY = f"{INDEX_VERSION}:" + hashlib.sha1(json.dumps(ABBREVIATIONS, sort_keys=True).encode("utf-8")).hexdigest()[:10]


def expand_abbreviations(text: str) -> str:
    """Expand exact word tokens only; leave unknown shorthand untouched."""
    if not text:
        return ""
    def repl(match: re.Match) -> str:
        token = match.group(0)
        return ABBREVIATIONS.get(token.upper(), token)
    return re.sub(r"\s+", " ", re.sub(r"\b[A-Za-z0-9]*[A-Za-z][A-Za-z0-9]*\b", repl, text)).strip()


def master_intended_title(layout_stem: str) -> str:
    stem = re.sub(r"^\s*\(\d+\)\s*", "", layout_stem or "").strip()
    return expand_abbreviations(stem)


DATA_DIR_ENV = "ZE_DETAIL_MANAGER_DATA_DIR"


# ---------------------------------------------------------------------------
# Categories: friendly groups worked out from the scrapbook number "(04)" at the
# start of each master's file name. Editable in categories.json next to this file.
# ---------------------------------------------------------------------------
DEFAULT_CATEGORIES = [
    {"numbers": ["01"], "name": "Foundation"},
    {"numbers": ["02"], "name": "Floor to Foundation"},
    {"numbers": ["03"], "name": "Floor to Floor"},
    {"numbers": ["04"], "name": "Floor to Beam", "sub": "Flush, Exterior"},
    {"numbers": ["05"], "name": "Floor to Beam", "sub": "Flush, Interior"},
    {"numbers": ["06"], "name": "Floor to Beam", "sub": "Bearing, Exterior"},
    {"numbers": ["07"], "name": "Floor to Beam", "sub": "Bearing, Interior"},
    {"numbers": ["08", "09", "10", "11", "12"], "name": "Roof"},
    {"numbers": ["13"], "name": "ZE Standards"},
    {"numbers": ["14"], "name": "Connections"},
]
OTHER_CATEGORY = "Other"
_CATEGORY_CACHE: dict = {"mtime": "unset", "cats": None, "error": ""}


def categories_path() -> Path:
    return Path(__file__).with_name("categories.json")


def _validate_categories(raw) -> List[dict]:
    items = raw.get("categories") if isinstance(raw, dict) else raw
    if not isinstance(items, list) or not items:
        raise ValueError('expected a "categories" list')
    out = []
    for i, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError(f"entry {i} is not a {{...}} block")
        name = str(item.get("name", "")).strip()
        if not name:
            raise ValueError(f"entry {i} has no name")
        numbers = item.get("numbers")
        if not isinstance(numbers, list) or not numbers:
            raise ValueError(f'entry {i} ("{name}") has no numbers list')
        try:
            nums = [int(str(n).strip()) for n in numbers]
        except ValueError:
            raise ValueError(f'entry {i} ("{name}") has a number that is not a number')
        out.append({"name": name, "sub": str(item.get("sub", "") or "").strip(), "numbers": nums})
    return out


def categories_config() -> List[dict]:
    """The category list; re-read when categories.json changes. A broken file
    never stops the program: the built-in list is used and a warning logged."""
    path = categories_path()
    try:
        mtime = path.stat().st_mtime_ns
    except OSError:
        mtime = None
    if _CATEGORY_CACHE["cats"] is not None and _CATEGORY_CACHE["mtime"] == mtime:
        return _CATEGORY_CACHE["cats"]
    cats, error = _validate_categories(DEFAULT_CATEGORIES), ""
    if mtime is not None:
        try:
            cats = _validate_categories(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
    if error:
        with contextlib.suppress(Exception):
            log_warning(f"categories.json could not be used ({error}); using the built-in category list")
    _CATEGORY_CACHE.update(mtime=mtime, cats=cats, error=error)
    return cats


def scrapbook_number(filename: str) -> Optional[int]:
    m = re.match(r"^\s*\((\d+)\)", filename or "")
    return int(m.group(1)) if m else None


def category_for_filename(filename: str, cats: Optional[List[dict]] = None) -> Tuple[str, str]:
    num = scrapbook_number(filename)
    for c in (cats if cats is not None else categories_config()):
        if num is not None and num in c["numbers"]:
            return c["name"], c["sub"]
    return OTHER_CATEGORY, ""


def category_matches(filename: str, key: str, cats: Optional[List[dict]] = None) -> bool:
    """key is a category name ("Floor to Beam": every sub-type) or "name|sub"."""
    name, sub = category_for_filename(filename, cats)
    return key == name or (bool(sub) and key == f"{name}|{sub}")


def app_data_dir() -> Path:
    # Optional override so a development copy can run beside the daily one.
    override = os.environ.get(DATA_DIR_ENV, "").strip()
    if override:
        return Path(override)
    base = os.environ.get("LOCALAPPDATA")
    return (Path(base) / APP_DIR_NAME) if base else (Path.home() / ".ze_detail_manager_poc07")


def localname(tag: str) -> str:
    return tag.split("}", 1)[-1]


def sanitize_filename(s: str, max_len: int = 150) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_.")
    return (s or "item")[:max_len]


def path_key(path: str) -> str:
    # Do not resolve mapped drives to another spelling.
    return hashlib.sha1(path.encode("utf-8", errors="surrogatepass")).hexdigest()[:16]


def rtf_to_text(rtf: str) -> str:
    if not rtf:
        return ""
    out: List[str] = []
    stack: List[Tuple[bool, int]] = []
    skip = False
    uc_skip = 1
    skip_plain = 0
    i = 0
    while i < len(rtf):
        c = rtf[i]
        if c == "{":
            stack.append((skip, uc_skip)); i += 1; continue
        if c == "}":
            if stack: skip, uc_skip = stack.pop()
            i += 1; continue
        if c != "\\":
            if skip_plain:
                skip_plain -= 1
            elif not skip and c not in "\r\n":
                out.append(c)
            i += 1; continue
        i += 1
        if i >= len(rtf): break
        c = rtf[i]
        if c in "\\{}":
            if not skip and not skip_plain: out.append(c)
            elif skip_plain: skip_plain -= 1
            i += 1; continue
        if c == "'" and i + 2 < len(rtf):
            try:
                ch = bytes.fromhex(rtf[i+1:i+3]).decode("cp1252", errors="replace")
                if not skip and not skip_plain: out.append(ch)
                elif skip_plain: skip_plain -= 1
            except Exception:
                pass
            i += 3; continue
        if c == "*":
            skip = True; i += 1; continue
        m = re.match(r"([A-Za-z]+)(-?\d+)? ?", rtf[i:])
        if m:
            word, arg = m.group(1), m.group(2); i += m.end()
            if word in DESTINATIONS:
                skip = True; continue
            if word == "uc" and arg is not None:
                with contextlib.suppress(Exception): uc_skip = max(0, int(arg))
                continue
            if word == "u" and arg is not None and not skip:
                with contextlib.suppress(Exception):
                    code = int(arg)
                    if code < 0: code += 65536
                    out.append(chr(code)); skip_plain = uc_skip
                continue
            if word in {"par", "line"} and not skip: out.append("\n"); continue
            if word == "tab" and not skip: out.append("\t"); continue
            if word == "emdash" and not skip: out.append("—"); continue
            if word == "endash" and not skip: out.append("–"); continue
            if word == "bullet" and not skip: out.append("•"); continue
            continue
        if not skip and c == "~": out.append(" ")
        i += 1
    lines = []
    for line in "".join(out).splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if line: lines.append(line)
    return "\n".join(lines)


def text_from_group(group: ET.Element) -> List[str]:
    texts = []
    for rep in group.iter(f"{{{NS['e']}}}rtfTextRep"):
        txt = rtf_to_text(rep.text or "")
        if txt: texts.append(txt)
    return texts


def _is_nts(text: str) -> bool:
    return re.sub(r"[^A-Za-z]", "", text or "").upper() in {"NTS", "NOTTOSCALE"}


def _plausible_title(text: str) -> bool:
    t = (text or "").strip()
    return len(t) >= 4 and not t.isdigit() and t.upper() != "XXX" and not _is_nts(t)


def is_noise_text(block: str) -> bool:
    """True for text boxes that say nothing about the detail: callout bubble and
    table-cell numbers on their own, "N.T.S.", and the "XXX" detail-number placeholder.
    Anything with real content ("2X6 STUD", "(2) A35", 2 1/4", "1/4") is kept."""
    t = re.sub(r"\s+", " ", block or "").strip()
    if not t: return True
    if re.fullmatch(r"\d{1,3}", t): return True
    if _is_nts(t): return True
    return t.upper() == "XXX"


def clean_text_blocks(text_items: Sequence[str]) -> List[str]:
    """The text worth searching and showing. The raw list is stored separately, untouched."""
    return [t for t in text_items if not is_noise_text(t)]


def infer_title_with_source(text_items: Sequence[str], scene_names: Sequence[str], page_name: str) -> Tuple[str, str]:
    """Return (title, source). source is 'drawing' (the title drawn on the detail),
    'scene' (SketchUp scene name) or 'page'."""
    # The library draws the title and "N.T.S." as two separate text boxes, the
    # title first. Use N.T.S. only as the marker; it is not part of the title.
    for i, block in enumerate(text_items):
        if i > 0 and _is_nts(block):
            candidate = re.sub(r"\s+", " ", text_items[i - 1]).strip()
            if _plausible_title(candidate):
                return candidate, "drawing"
    for block in reversed(text_items):
        lines = [re.sub(r"\s+", " ", x).strip() for x in block.splitlines() if x.strip()]
        for i, line in enumerate(lines):
            if _is_nts(line) and i > 0 and _plausible_title(lines[i - 1]):
                return lines[i - 1], "drawing"
    for scene in scene_names:
        if scene.strip(): return scene.strip(), "scene"
    return (page_name, "page") if page_name else ("Untitled Detail", "page")


def infer_title(text_items: Sequence[str], scene_names: Sequence[str], page_name: str) -> str:
    return infer_title_with_source(text_items, scene_names, page_name)[0]


def _infer_title_poc07a(text_items: Sequence[str], scene_names: Sequence[str], page_name: str) -> str:
    """Prototype 0.1 rule, kept for reference and comparison only."""
    for block in reversed(text_items):
        lines = [re.sub(r"\s+", " ", x).strip() for x in block.splitlines() if x.strip()]
        for i, line in enumerate(lines):
            compact = re.sub(r"[^A-Za-z]", "", line).upper()
            if compact in {"NTS", "NOTTOSCALE"} and i > 0:
                candidate = lines[i-1]
                if len(candidate) >= 4 and not candidate.isdigit():
                    return candidate
    for scene in scene_names:
        if scene.strip(): return scene.strip()
    return page_name or "Untitled Detail"


def floats_from_csv(s: Optional[str]) -> List[float]:
    vals = []
    if s:
        for token in s.split(","):
            with contextlib.suppress(Exception): vals.append(float(token))
    return vals


def group_bounds(group: ET.Element) -> Optional[List[float]]:
    xs, ys = [], []
    for rb in group.iter(f"{{{NS['e']}}}rectangleBase"):
        try:
            x, y = float(rb.get("x", "nan")), float(rb.get("y", "nan"))
            w, h = float(rb.get("width", "nan")), float(rb.get("height", "nan"))
            xs += [x, x+w]; ys += [y, y+h]
        except Exception:
            pass
    for pts in group.iter(f"{{{NS['e']}}}points2f"):
        vals = floats_from_csv(pts.text)
        xs += vals[0::2]; ys += vals[1::2]
    return [min(xs), min(ys), max(xs), max(ys)] if xs and ys else None


def all_entity_ids(group: ET.Element) -> List[str]:
    return [el.get("id") for el in group.iter() if el.get("id")]


def child_by_local(parent: ET.Element, name: str) -> Optional[ET.Element]:
    for c in list(parent):
        if localname(c.tag) == name: return c
    return None


def attr_by_local(el: ET.Element, name: str) -> Optional[str]:
    for k, v in el.attrib.items():
        if localname(k) == name: return v
    return None


def iter_local(root: ET.Element, name: str):
    for el in root.iter():
        if localname(el.tag) == name: yield el


class LibraryDB:
    def __init__(self, root: Path):
        self.root = root
        self.db_path = root / "detail_library.sqlite"
        self.preview_root = root / "previews"
        self.full_preview_root = root / "full_previews"
        self.staging_root = root / "staging"
        self.render_root = root / "thumbnail_renders"
        self.thumbnail_job_root = root / "thumbnail_jobs"
        self.config_path = root / "config.json"
        for p in (root, self.preview_root, self.full_preview_root, self.staging_root, self.render_root, self.thumbnail_job_root):
            p.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self):
        con = sqlite3.connect(self.db_path, timeout=30)
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self):
        con = self.connect(); cur = con.cursor()
        cur.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS layout_files (
          layout_file TEXT PRIMARY KEY, layout_filename TEXT, size_bytes INTEGER,
          mtime_ns INTEGER, page_count INTEGER, detail_count INTEGER,
          skp_reference_count INTEGER, last_indexed_utc TEXT, last_error TEXT);
        CREATE TABLE IF NOT EXISTS skp_references (
          layout_file TEXT, skp_ref_id TEXT, external_path_exact TEXT,
          internal_target TEXT, PRIMARY KEY(layout_file, skp_ref_id));
        CREATE TABLE IF NOT EXISTS details (
          detail_key TEXT PRIMARY KEY, layout_file TEXT, layout_filename TEXT,
          page_ref_id TEXT, page_xml TEXT, page_name TEXT, page_index INTEGER, group_index INTEGER,
          viewport_count INTEGER, primary_viewport_id TEXT, primary_scene_name TEXT,
          primary_scene_pid TEXT, display_title TEXT, expanded_title TEXT,
          master_title TEXT, skp_paths_exact TEXT, bounds_json TEXT,
          full_preview_relpath TEXT, searchable_text TEXT);
        CREATE TABLE IF NOT EXISTS viewports (
          detail_key TEXT, viewport_id TEXT, scene_name TEXT, scene_pid TEXT,
          skp_ref_id TEXT, image_ref_id TEXT, vector_ref_id TEXT, preview_relpath TEXT,
          PRIMARY KEY(detail_key, viewport_id));
        """)
        detail_cols = {r[1] for r in cur.execute("PRAGMA table_info(details)")}
        for col in ("raw_text", "clean_text"):
            if col not in detail_cols: cur.execute(f"ALTER TABLE details ADD COLUMN {col} TEXT DEFAULT ''")
        if "index_version" not in {r[1] for r in cur.execute("PRAGMA table_info(layout_files)")}:
            cur.execute("ALTER TABLE layout_files ADD COLUMN index_version INTEGER DEFAULT 0")
        with contextlib.suppress(sqlite3.OperationalError):
            cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS detail_search USING fts5(detail_key UNINDEXED, searchable_text)")
        con.commit(); con.close()

    def get_config(self) -> dict:
        if self.config_path.exists():
            with contextlib.suppress(Exception): return json.loads(self.config_path.read_text(encoding="utf-8"))
        return {}

    def save_config(self, data: dict):
        current = self.get_config()
        current.update(data)
        self.config_path.write_text(json.dumps(current, indent=2), encoding="utf-8")

    def remove_layout(self, con: sqlite3.Connection, layout_file: str):
        keys = [r[0] for r in con.execute("SELECT detail_key FROM details WHERE layout_file=?", (layout_file,))]
        for k in keys:
            with contextlib.suppress(sqlite3.OperationalError): con.execute("DELETE FROM detail_search WHERE detail_key=?", (k,))
        con.execute("DELETE FROM viewports WHERE detail_key IN (SELECT detail_key FROM details WHERE layout_file=?)", (layout_file,))
        con.execute("DELETE FROM details WHERE layout_file=?", (layout_file,))
        con.execute("DELETE FROM skp_references WHERE layout_file=?", (layout_file,))
        con.execute("DELETE FROM layout_files WHERE layout_file=?", (layout_file,))
        shutil.rmtree(self.preview_root / path_key(layout_file), ignore_errors=True)
        shutil.rmtree(self.full_preview_root / path_key(layout_file), ignore_errors=True)
        shutil.rmtree(self.render_root / path_key(layout_file), ignore_errors=True)


DB = LibraryDB(app_data_dir())

# ---------------------------------------------------------------------------
# Diagnostics log. Lives in the app-data folder only - never in the library
# or in job folders.
# ---------------------------------------------------------------------------
LOG = logging.getLogger("detail_manager")
LOG_PATH: Optional[Path] = None
LOG_SETUP_ERROR = ""


def setup_logging(root: Path) -> Optional[Path]:
    """Attach a small rotating log file under <app data>/logs. Never raises."""
    global LOG_PATH, LOG_SETUP_ERROR
    for h in list(LOG.handlers):
        LOG.removeHandler(h)
        with contextlib.suppress(Exception): h.close()
    LOG.setLevel(logging.INFO)
    LOG.propagate = False
    try:
        log_dir = root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / "detail_manager.log"
        handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S"))
        LOG.addHandler(handler)
        LOG_PATH, LOG_SETUP_ERROR = path, ""
    except Exception as exc:  # the program must still run without a log
        LOG.addHandler(logging.NullHandler())
        LOG_PATH, LOG_SETUP_ERROR = None, f"{type(exc).__name__}: {exc}"
    return LOG_PATH


def _one_line(text) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def log_info(msg: str): LOG.info(_one_line(msg))
def log_warning(msg: str): LOG.warning(_one_line(msg))
def log_error(msg: str): LOG.error(_one_line(msg))


def read_log_tail(max_lines: int = 300) -> List[dict]:
    """Newest-last list of {time, level, message} from the current log file."""
    if not LOG_PATH or not LOG_PATH.exists():
        return []
    for h in LOG.handlers:
        with contextlib.suppress(Exception): h.flush()
    try:
        lines = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]
    except Exception:
        return []
    out = []
    for line in lines:
        m = re.match(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) (\w+)\s+(.*)$", line)
        if m: out.append({"time": m.group(1), "level": m.group(2), "message": m.group(3)})
        elif out: out[-1]["message"] += " " + line.strip()
    return out


setup_logging(DB.root)
INDEX_STATE = {"running": False, "total": 0, "done": 0, "current": "", "message": "", "errors": [], "changed": 0, "unchanged": 0, "reread": 0}
INDEX_LOCK = threading.Lock()


def parse_layout(layout_path: Path, preview_dir: Path) -> Tuple[dict, List[dict]]:
    # Preserve the path spelling used to discover the file; no Path.resolve().
    layout_file = str(layout_path)
    stat = layout_path.stat()
    preview_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(layout_path, "r") as z:
        names = set(z.namelist())
        if not {"document.xml", "references.xml"}.issubset(names): raise ValueError("Not a recognized LayOut package")
        doc_root = ET.fromstring(z.read("document.xml")); ref_root = ET.fromstring(z.read("references.xml"))
        page_meta = {}
        for pr in doc_root.findall(".//ld:pageRef", NS):
            page_meta[pr.get(R_ID, "")] = {"page_name": pr.get("name", ""), "page_id": pr.get("id", "")}
        page_refs, skp_refs, image_refs, vector_refs = {}, {}, {}, {}
        for el in list(ref_root):
            kind, rid = localname(el.tag), el.get(R_ID, "")
            rec = {"id": rid, "internalTarget": el.get("internalTarget", ""), "externalTarget": el.get("externalTarget", "")}
            if kind == "pageFileReference": page_refs[rid] = rec
            elif kind == "skpFileReference": skp_refs[rid] = rec
            elif kind == "imageFileReference": image_refs[rid] = rec
            elif kind == "vectorFileReference": vector_refs[rid] = rec
        details = []
        ordered_pages = [pr.get(R_ID, "") for pr in doc_root.findall(".//ld:pageRef", NS)]
        for page_index, page_ref_id in enumerate(ordered_pages, start=1):
            pref = page_refs.get(page_ref_id)
            if not pref: continue
            page_xml = pref.get("internalTarget", "")
            if not page_xml or page_xml not in names: continue
            page_root = ET.fromstring(z.read(page_xml)); page_name = page_meta.get(page_ref_id, {}).get("page_name", "")
            top_list = page_root.find("p:layerEntityManager/p:entityList", NS)
            if top_list is None: continue
            group_index = 0
            for entity in list(top_list):
                if entity.tag != f"{{{NS['e']}}}group": continue
                group_index += 1
                models = list(entity.iter(f"{{{NS['e']}}}skpModelRef"))
                if not models: continue
                viewports, skp_paths, skp_ids, scene_names = [], [], [], []
                for sm in models:
                    skp_el = sm.find("r:skpFileReference", NS); img_el = sm.find("r:imageFileReference", NS); vec_el = sm.find("r:vectorFileReference", NS)
                    sid = skp_el.get(R_ID, "") if skp_el is not None else ""; iid = img_el.get(R_ID, "") if img_el is not None else ""; vid = vec_el.get(R_ID, "") if vec_el is not None else ""
                    scene, scene_pid, viewport_id = sm.get("defaultPageName", ""), sm.get("defaultPagePID", ""), sm.get("id", "")
                    if scene: scene_names.append(scene)
                    if sid and sid not in skp_ids:
                        skp_ids.append(sid); ext = skp_refs.get(sid, {}).get("externalTarget", "")
                        if ext not in skp_paths: skp_paths.append(ext)
                    rel = ""
                    internal = image_refs.get(iid, {}).get("internalTarget", "")
                    if internal and internal in names:
                        out_name = sanitize_filename(f"{page_ref_id}__{viewport_id}__{scene}.png")
                        out_path = preview_dir / out_name
                        with z.open(internal) as src, out_path.open("wb") as dst: shutil.copyfileobj(src, dst)
                        rel = str(out_path.relative_to(DB.preview_root)).replace(os.sep, "/")
                    viewports.append({"viewport_id": viewport_id, "scene_name": scene, "scene_pid": scene_pid, "skp_ref_id": sid, "image_ref_id": iid, "vector_ref_id": vid, "preview_relpath": rel})
                texts = text_from_group(entity); title, title_source = infer_title_with_source(texts, scene_names, page_name); primary = viewports[0]
                # A title drawn on the detail is already plain English: leave it alone.
                # Shorthand expansion is only for scene/page names used as a fallback.
                expanded_title = title if title_source == "drawing" else expand_abbreviations(title)
                master_title = master_intended_title(layout_path.stem)
                detail_key = f"{layout_file}|{page_ref_id}|{primary['viewport_id']}"
                clean = clean_text_blocks(texts)
                searchable = "\n".join(filter(None, [layout_path.stem, master_title, page_name, expand_abbreviations(page_name), title, expanded_title, *scene_names, *(expand_abbreviations(x) for x in scene_names), *clean]))
                details.append({"detail_key": detail_key, "layout_file": layout_file, "layout_filename": layout_path.name, "page_ref_id": page_ref_id, "page_xml": page_xml, "page_name": page_name, "page_index": page_index, "group_index": group_index, "viewport_count": len(viewports), "primary_viewport_id": primary["viewport_id"], "primary_scene_name": primary["scene_name"], "primary_scene_pid": primary["scene_pid"], "display_title": title, "expanded_title": expanded_title, "master_title": master_title, "skp_paths_exact": skp_paths, "bounds": group_bounds(entity), "full_preview_relpath": "", "searchable_text": searchable, "raw_text": "\n".join(texts), "clean_text": "\n".join(clean), "viewports": viewports})
        return ({"layout_file": layout_file, "layout_filename": layout_path.name, "size_bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns, "page_count": len(ordered_pages), "detail_count": len(details), "skp_reference_count": len(skp_refs), "skp_references": skp_refs}, details)


def index_library(library_root: str):
    with INDEX_LOCK: INDEX_STATE.update({"running": True, "total": 0, "done": 0, "current": "", "message": "Scanning library...", "errors": [], "changed": 0, "unchanged": 0, "reread": 0})
    try:
        root = Path(library_root)
        # Safety: an unreachable library must never be read as "every master was deleted".
        if not root.is_dir(): raise FileNotFoundError(f"Library folder not reachable: {library_root}")
        log_info(f"Index refresh started: {library_root}")
        files = sorted(p for p in root.rglob("*.layout") if p.is_file()); con = DB.connect()
        existing = {r["layout_file"]: dict(r) for r in con.execute("SELECT * FROM layout_files")}; discovered = {str(p): p for p in files}
        for old in list(existing):
            if old not in discovered:
                DB.remove_layout(con, old); log_info(f"Removed from index (master no longer in library): {old}")
        con.commit()
        with INDEX_LOCK: INDEX_STATE.update({"total": len(files), "message": f"Found {len(files)} LayOut files"})
        for i, p in enumerate(files, 1):
            path_str, st = str(p), p.stat(); old = existing.get(path_str)
            file_same = bool(old and old.get("size_bytes") == st.st_size and old.get("mtime_ns") == st.st_mtime_ns and not old.get("last_error"))
            unchanged = file_same and str(old.get("index_version") or "") == READ_RULES_KEY
            with INDEX_LOCK: INDEX_STATE.update({"done": i-1, "current": p.name})
            if unchanged:
                with INDEX_LOCK: INDEX_STATE["unchanged"] += 1
                continue
            temp_preview = DB.preview_root / (path_key(path_str) + "_tmp"); final_preview = DB.preview_root / path_key(path_str)
            shutil.rmtree(temp_preview, ignore_errors=True); temp_preview.mkdir(parents=True, exist_ok=True)
            try:
                summary, details = parse_layout(p, temp_preview)
                for d in details:
                    for vp in d["viewports"]:
                        if vp["preview_relpath"]: vp["preview_relpath"] = vp["preview_relpath"].replace(path_key(path_str)+"_tmp/", path_key(path_str)+"/", 1)
                if file_same:
                    # Only the reading rules changed, not the master: keep its full thumbnails.
                    kept = {r[0]: r[1] or "" for r in con.execute("SELECT detail_key, full_preview_relpath FROM details WHERE layout_file=?", (path_str,))}
                    for d in details: d["full_preview_relpath"] = kept.get(d["detail_key"], "")
                con.execute("BEGIN")
                keys = [r[0] for r in con.execute("SELECT detail_key FROM details WHERE layout_file=?", (path_str,))]
                for k in keys:
                    with contextlib.suppress(sqlite3.OperationalError): con.execute("DELETE FROM detail_search WHERE detail_key=?", (k,))
                con.execute("DELETE FROM viewports WHERE detail_key IN (SELECT detail_key FROM details WHERE layout_file=?)", (path_str,)); con.execute("DELETE FROM details WHERE layout_file=?", (path_str,)); con.execute("DELETE FROM skp_references WHERE layout_file=?", (path_str,)); con.execute("DELETE FROM layout_files WHERE layout_file=?", (path_str,))
                con.execute("INSERT INTO layout_files (layout_file,layout_filename,size_bytes,mtime_ns,page_count,detail_count,skp_reference_count,last_indexed_utc,last_error,index_version) VALUES (?,?,?,?,?,?,?,?,?,?)", (path_str, p.name, summary["size_bytes"], summary["mtime_ns"], summary["page_count"], summary["detail_count"], summary["skp_reference_count"], datetime.now(timezone.utc).isoformat(), "", READ_RULES_KEY))
                for rid, r in summary["skp_references"].items(): con.execute("INSERT INTO skp_references VALUES (?,?,?,?)", (path_str, rid, r.get("externalTarget", ""), r.get("internalTarget", "")))
                for d in details:
                    con.execute("INSERT INTO details (detail_key,layout_file,layout_filename,page_ref_id,page_xml,page_name,page_index,group_index,viewport_count,primary_viewport_id,primary_scene_name,primary_scene_pid,display_title,expanded_title,master_title,skp_paths_exact,bounds_json,full_preview_relpath,searchable_text,raw_text,clean_text) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (d["detail_key"], d["layout_file"], d["layout_filename"], d["page_ref_id"], d["page_xml"], d["page_name"], d["page_index"], d["group_index"], d["viewport_count"], d["primary_viewport_id"], d["primary_scene_name"], d["primary_scene_pid"], d["display_title"], d["expanded_title"], d["master_title"], json.dumps(d["skp_paths_exact"]), json.dumps(d["bounds"]), d["full_preview_relpath"], d["searchable_text"], d["raw_text"], d["clean_text"]))
                    with contextlib.suppress(sqlite3.OperationalError): con.execute("INSERT INTO detail_search(detail_key, searchable_text) VALUES (?,?)", (d["detail_key"], d["searchable_text"]))
                    for vp in d["viewports"]: con.execute("INSERT INTO viewports VALUES (?,?,?,?,?,?,?,?)", (d["detail_key"], vp["viewport_id"], vp["scene_name"], vp["scene_pid"], vp["skp_ref_id"], vp["image_ref_id"], vp["vector_ref_id"], vp["preview_relpath"]))
                con.commit()
                shutil.rmtree(final_preview, ignore_errors=True)
                temp_preview.rename(final_preview)
                if not file_same:
                    shutil.rmtree(DB.full_preview_root / path_key(path_str), ignore_errors=True)
                    shutil.rmtree(DB.render_root / path_key(path_str), ignore_errors=True)
                with INDEX_LOCK: INDEX_STATE["reread" if file_same else "changed"] += 1
            except Exception as exc:
                con.rollback(); shutil.rmtree(temp_preview, ignore_errors=True); msg = f"{type(exc).__name__}: {exc}"
                if not old:
                    con.execute("INSERT OR REPLACE INTO layout_files (layout_file,layout_filename,size_bytes,mtime_ns,page_count,detail_count,skp_reference_count,last_indexed_utc,last_error,index_version) VALUES (?,?,?,?,?,?,?,?,?,?)", (path_str, p.name, st.st_size, st.st_mtime_ns, 0, 0, 0, datetime.now(timezone.utc).isoformat(), msg, READ_RULES_KEY)); con.commit()
                with INDEX_LOCK: INDEX_STATE["errors"].append({"file": path_str, "error": msg})
                log_error(f"Index failed for {path_str}: {msg}" + (" (earlier index data for this master was kept)" if old else ""))
            finally:
                with INDEX_LOCK: INDEX_STATE["done"] = i
        con.close(); DB.save_config({"library_root": library_root})
        with INDEX_LOCK:
            reread_note = f", {INDEX_STATE['reread']} re-read with the new rules (thumbnails kept)" if INDEX_STATE["reread"] else ""
            INDEX_STATE["message"] = f"Refresh complete: {INDEX_STATE['changed']} changed, {INDEX_STATE['unchanged']} unchanged{reread_note}"
            summary_line = f"Index refresh complete: {len(files)} master(s), {INDEX_STATE['changed']} changed, {INDEX_STATE['unchanged']} unchanged{reread_note}, {len(INDEX_STATE['errors'])} error(s)"
        log_info(summary_line)
    except Exception as exc:
        # Runs on a background thread: without this the failure would vanish.
        msg = f"{type(exc).__name__}: {exc}"
        log_error(f"Index refresh stopped: {msg}")
        with INDEX_LOCK:
            INDEX_STATE["message"] = f"Refresh failed: {msg}"
            INDEX_STATE["errors"].append({"file": library_root, "error": msg})
    finally:
        with INDEX_LOCK: INDEX_STATE.update({"running": False, "current": ""})


def _dom_element_children(node):
    return [c for c in node.childNodes if c.nodeType == Node.ELEMENT_NODE]


def _dom_first_direct(node, local_name: str):
    if node is None:
        return None
    for c in _dom_element_children(node):
        if c.localName == local_name:
            return c
    return None


def _dom_desc(node, local_name: Optional[str] = None, namespace: Optional[str] = None):
    out = []
    if node is None:
        return out
    for el in node.getElementsByTagName("*"):
        if local_name is not None and el.localName != local_name:
            continue
        if namespace is not None and el.namespaceURI != namespace:
            continue
        out.append(el)
    return out


def _dom_attr_by_local(el, local_name: str) -> Optional[str]:
    if el is None or not el.hasAttributes():
        return None
    for i in range(el.attributes.length):
        a = el.attributes.item(i)
        if a.localName == local_name:
            return a.value
    return None


def _dom_bytes(doc) -> bytes:
    raw = doc.toxml(encoding="UTF-8", standalone=True)
    return raw.replace(b"?>", b"?>\n", 1)


def validate_staging_package(path: Path) -> List[str]:
    errors: List[str] = []
    try:
        with zipfile.ZipFile(path, "r") as z:
            bad = z.testzip()
            if bad:
                errors.append(f"ZIP CRC error in {bad}")
            names = set(z.namelist())
            for required in ("document.xml", "references.xml", "documentProperties.xml"):
                if required not in names:
                    errors.append(f"Missing required package member: {required}")
            if errors:
                return errors

            refs_doc = minidom.parseString(z.read("references.xml"))
            ref_ids = {}
            for ref in _dom_element_children(refs_doc.documentElement):
                rid = ref.getAttributeNS(NS["r"], "id")
                if rid:
                    ref_ids[rid] = (ref.localName, ref.getAttribute("internalTarget"))
                    internal = ref.getAttribute("internalTarget")
                    if internal and internal not in names:
                        errors.append(f"{ref.localName} {rid} points to missing payload {internal}")

            doc = minidom.parseString(z.read("document.xml"))
            for pr in _dom_desc(doc.documentElement, "pageRef"):
                rid = pr.getAttributeNS(NS["r"], "id")
                if rid and rid not in ref_ids:
                    errors.append(f"Document pageRef {rid} is missing from references.xml")

            page_files = [n for n in names if n.startswith("pages/") and n.endswith(".xml")]
            if len(page_files) != 1:
                errors.append(f"Expected 1 page XML in staging file; found {len(page_files)}")

            for page_name in page_files:
                page_doc = minidom.parseString(z.read(page_name))
                for el in _dom_desc(page_doc.documentElement):
                    if el.localName in {"skpFileReference", "imageFileReference", "vectorFileReference"}:
                        rid = el.getAttributeNS(NS["r"], "id")
                        if rid and rid not in ref_ids:
                            errors.append(f"{page_name}: {el.localName} {rid} missing from references.xml")
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    return errors


def build_staging(detail_key: str) -> Path:
    con = DB.connect(); d = con.execute("SELECT * FROM details WHERE detail_key=?", (detail_key,)).fetchone(); con.close()
    if not d:
        raise ValueError("Detail not found in local index")
    src = Path(d["layout_file"])
    if not src.exists():
        raise FileNotFoundError(f"Master LayOut file not found: {src}")

    page_xml, target_page_ref, target_viewport_id = d["page_xml"], d["page_ref_id"], d["primary_viewport_id"]

    with zipfile.ZipFile(src, "r") as zin:
        infos = {i.filename: i for i in zin.infolist()}
        data = {i.filename: zin.read(i.filename) for i in zin.infolist()}

    if page_xml not in data:
        raise ValueError(f"Indexed page payload missing: {page_xml}")

    page_doc = minidom.parseString(data[page_xml])
    page_root = page_doc.documentElement
    page_mgr = _dom_first_direct(page_root, "layerEntityManager")
    top_list = _dom_first_direct(page_mgr, "entityList")
    if top_list is None:
        raise ValueError("Could not find page entity list")

    groups = [x for x in _dom_element_children(top_list) if x.localName == "group"]
    target_group = None
    for child in groups:
        for sm in _dom_desc(child, "skpModelRef", NS["e"]):
            if sm.getAttribute("id") == target_viewport_id:
                target_group = child
                break
        if target_group is not None:
            break

    if target_group is None:
        idx = int(d["group_index"]) - 1
        if 0 <= idx < len(groups):
            target_group = groups[idx]
    if target_group is None:
        raise ValueError("Could not locate detail group")

    keep_entity_ids = set()
    target_ref_ids = set()
    target_skp_ids = set()
    for el in [target_group] + _dom_desc(target_group):
        if el.hasAttribute("id"):
            keep_entity_ids.add(el.getAttribute("id"))
        if el.hasAttributes():
            for i in range(el.attributes.length):
                a = el.attributes.item(i)
                if a.namespaceURI == NS["r"] and a.localName == "id":
                    target_ref_ids.add(a.value)
        if el.localName == "skpFileReference" and el.namespaceURI == NS["r"]:
            rid = el.getAttributeNS(NS["r"], "id")
            if rid:
                target_skp_ids.add(rid)

    # Keep the entire detail group intact, including all 1–5+ SketchUp viewports.
    for child in _dom_element_children(top_list):
        if child is not target_group:
            top_list.removeChild(child)

    for li in _dom_desc(page_root, "layerInstance"):
        ent_list = _dom_first_direct(li, "entityList")
        if ent_list is not None:
            for er in _dom_element_children(ent_list):
                if _dom_attr_by_local(er, "ref") not in keep_entity_ids:
                    ent_list.removeChild(er)

    data[page_xml] = _dom_bytes(page_doc)

    doc = minidom.parseString(data["document.xml"])
    root = doc.documentElement
    page_manager = next(iter(_dom_desc(root, "pageManager")), None)
    if page_manager is not None:
        for pr in _dom_element_children(page_manager):
            if pr.getAttributeNS(NS["r"], "id") != target_page_ref:
                page_manager.removeChild(pr)

    for el in _dom_desc(root, "autoTextDefinition"):
        if el.getAttribute("name") == "PageNumber":
            el.setAttributeNS(NS["l"], "l:ref", target_page_ref)
    for el in _dom_desc(root, "lastPageDisplayed"):
        el.setAttributeNS(NS["l"], "l:ref", target_page_ref)

    doc_layer_mgr = _dom_first_direct(root, "layerEntityManager")
    if doc_layer_mgr is not None:
        direct = _dom_first_direct(doc_layer_mgr, "entityList")
        if direct is not None:
            for child in _dom_element_children(direct):
                direct.removeChild(child)
        for li in _dom_desc(doc_layer_mgr, "layerInstance"):
            ent_list = _dom_first_direct(li, "entityList")
            if ent_list is not None:
                for child in _dom_element_children(ent_list):
                    ent_list.removeChild(child)

    connection_manager = next(iter(_dom_desc(root, "connectionManager")), None)
    if connection_manager is not None:
        for conn in _dom_element_children(connection_manager):
            refs = set()
            for el in [conn] + _dom_desc(conn):
                if not el.hasAttributes():
                    continue
                for i in range(el.attributes.length):
                    a = el.attributes.item(i)
                    if a.localName == "ref":
                        refs.add(a.value)
            if not refs or not refs.issubset(keep_entity_ids):
                connection_manager.removeChild(conn)

    data["document.xml"] = _dom_bytes(doc)

    if "documentProperties.xml" in data:
        props = minidom.parseString(data["documentProperties.xml"])
        for stat in _dom_desc(props.documentElement, "documentStatistic"):
            stat.setAttribute("pageCount", "1")
        data["documentProperties.xml"] = _dom_bytes(props)

    refs_doc = minidom.parseString(data["references.xml"])
    refs_root = refs_doc.documentElement
    removed_payloads = set()
    for ref in _dom_element_children(refs_root):
        kind = ref.localName
        rid = ref.getAttributeNS(NS["r"], "id")
        remove = False
        if kind == "pageFileReference":
            remove = rid != target_page_ref
        elif kind in {"imageFileReference", "vectorFileReference"}:
            remove = rid not in target_ref_ids
        elif kind == "skpFileReference" and target_skp_ids:
            remove = rid not in target_skp_ids

        if remove:
            internal = ref.getAttribute("internalTarget")
            if internal:
                removed_payloads.add(internal)
            refs_root.removeChild(ref)

    data["references.xml"] = _dom_bytes(refs_doc)

    keep_names = {
        n for n in data
        if not (n.startswith("pages/") and n.endswith(".xml") and n != page_xml)
    }
    keep_names -= removed_payloads

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    title = sanitize_filename(d["expanded_title"] or d["display_title"], 70)
    out = DB.staging_root / f"DM_{ts}__{title}.layout"

    with zipfile.ZipFile(out, "w") as zout:
        for name, old in infos.items():
            if name not in keep_names:
                continue
            zi = zipfile.ZipInfo(name, date_time=old.date_time)
            zi.compress_type = old.compress_type
            zi.comment = old.comment
            zi.extra = old.extra
            zi.internal_attr = old.internal_attr
            zi.external_attr = old.external_attr
            zi.create_system = old.create_system
            zi.flag_bits = old.flag_bits
            zout.writestr(zi, data[name])

    errors = validate_staging_package(out)
    if errors:
        with contextlib.suppress(Exception):
            out.unlink()
        raise ValueError("Staging package validation failed: " + "; ".join(errors[:6]))

    return out


def cleanup_staging(hours: int = 24) -> int:
    cutoff, count = time.time() - hours*3600, 0
    for p in DB.staging_root.glob("*.layout"):
        try:
            if p.stat().st_mtime < cutoff: p.unlink(); count += 1
        except Exception: pass
    return count


def windows_open(path: str):
    runtime_path = path
    if os.name == "nt":
        runtime_path = runtime_path.replace("/", "\\")
        os.startfile(runtime_path)  # type: ignore[attr-defined]
    else:
        print(f"DEV open: {runtime_path}")


def safe_search_query(q: str) -> str:
    return " AND ".join(f'"{t}"*' for t in re.findall(r"[A-Za-z0-9]+", q))


def category_layout_files(category: str) -> List[str]:
    cats = categories_config()
    con = DB.connect()
    rows = con.execute("SELECT layout_file, layout_filename FROM layout_files").fetchall()
    con.close()
    return [r[0] for r in rows if category_matches(r[1], category, cats)]


def search_details(q: str = "", source: str = "", limit: int = 80, category: str = "") -> List[dict]:
    cat_files = category_layout_files(category) if category else None
    if cat_files == []:
        return []
    cat_sql = f"d.layout_file IN ({','.join('?' * len(cat_files))})" if cat_files else ""
    con = DB.connect(); params, joins, where = [], "", []; order = "d.layout_filename,d.page_name,d.group_index"
    if q.strip():
        ftsq = safe_search_query(q)
        if ftsq:
            joins = " JOIN detail_search s ON s.detail_key=d.detail_key "; where.append("s.searchable_text MATCH ?"); params.append(ftsq); order = "bm25(detail_search),d.layout_filename,d.page_name,d.group_index"
    if source: where.append("d.layout_file=?"); params.append(source)
    if cat_files: where.append(cat_sql); params += cat_files
    sql = "SELECT d.* FROM details d" + joins + ((" WHERE " + " AND ".join(where)) if where else "") + " ORDER BY " + order + " LIMIT ?"; params.append(limit)
    try: rows = con.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        params, where = [], []
        if q.strip(): where.append("d.searchable_text LIKE ?"); params.append(f"%{q}%")
        if source: where.append("d.layout_file=?"); params.append(source)
        if cat_files: where.append(cat_sql); params += cat_files
        sql = "SELECT d.* FROM details d" + ((" WHERE " + " AND ".join(where)) if where else "") + " ORDER BY d.layout_filename,d.page_name,d.group_index LIMIT ?"; params.append(limit); rows = con.execute(sql, params).fetchall()
    out = []
    for r in rows:
        item = dict(r); item["skp_paths_exact"] = json.loads(item["skp_paths_exact"] or "[]"); item["viewports"] = [dict(x) for x in con.execute("SELECT * FROM viewports WHERE detail_key=? ORDER BY rowid", (r["detail_key"],))]; item["scene_label"] = scene_label(item); item["notes_text"] = notes_text(item); out.append(item)
    con.close(); return out


def scene_label(item: dict) -> str:
    """Short second line for a card: the SketchUp scene in plain words. Empty when
    it would only repeat the title (details whose title came from the scene)."""
    scene = expand_abbreviations(item.get("primary_scene_name") or "")
    if not scene or scene in {item.get("expanded_title"), item.get("display_title")}:
        return ""
    extra = max(0, int(item.get("viewport_count") or 1) - 1)
    return scene + (f" (+{extra} more view{'s' if extra != 1 else ''})" if extra else "")


def notes_text(item: dict) -> str:
    """Notes shown in the detail window: the clean text without the title line.
    Empty for details indexed before clean text existed (the window then shows the old text)."""
    lines = (item.get("clean_text") or "").split("\n")
    title = item.get("display_title") or ""
    if title in lines: lines.remove(title)
    return "\n".join(x for x in lines if x.strip())


def library_categories() -> List[dict]:
    """Sidebar groups with detail counts, in categories.json order, "Other" last.
    Only categories that contain details are listed."""
    cats = categories_config()
    con = DB.connect()
    rows = con.execute("SELECT layout_filename, detail_count FROM layout_files WHERE detail_count>0").fetchall()
    con.close()
    groups: Dict[str, dict] = {}
    for filename, count in rows:
        name, sub = category_for_filename(filename, cats)
        g = groups.setdefault(name, {"key": name, "name": name, "count": 0, "subs": {}})
        g["count"] += count or 0
        if sub:
            g["subs"][sub] = g["subs"].get(sub, 0) + (count or 0)
    order = list(dict.fromkeys([c["name"] for c in cats] + [OTHER_CATEGORY]))
    out = []
    for name in order:
        g = groups.get(name)
        if not g:
            continue
        sub_order = list(dict.fromkeys(c["sub"] for c in cats if c["name"] == name and c["sub"]))
        g["children"] = [{"key": f"{name}|{s}", "sub": s, "count": g["subs"][s]} for s in sub_order if s in g["subs"]]
        del g["subs"]
        out.append(g)
    return out


def library_sources() -> List[dict]:
    con = DB.connect(); rows = [dict(r) for r in con.execute("SELECT layout_file,layout_filename,detail_count,last_error FROM layout_files ORDER BY layout_filename")]; con.close(); return rows


def thumbnail_hidden_layers() -> List[str]:
    cfg = DB.get_config()
    raw = cfg.get("thumbnail_hidden_layers", ["GUIDES"])
    if isinstance(raw, str):
        raw = [x.strip() for x in raw.split(",")]
    if not isinstance(raw, list):
        raw = ["GUIDES"]
    out = []
    for value in raw:
        name = str(value).strip()
        if name and name.lower() not in {x.lower() for x in out}:
            out.append(name)
    return out or ["GUIDES"]


def save_thumbnail_hidden_layers(values: Sequence[str]) -> List[str]:
    cleaned = []
    for value in values:
        name = str(value).strip()
        if name and name.lower() not in {x.lower() for x in cleaned}:
            cleaned.append(name)
    if not cleaned:
        cleaned = ["GUIDES"]
    DB.save_config({"thumbnail_hidden_layers": cleaned})
    return cleaned


def thumbnail_status() -> dict:
    con = DB.connect()
    total = con.execute("SELECT COUNT(*) FROM details").fetchone()[0]
    full = con.execute("SELECT COUNT(*) FROM details WHERE COALESCE(full_preview_relpath,'')<>''").fetchone()[0]
    files = con.execute("SELECT COUNT(*) FROM layout_files WHERE detail_count>0 AND COALESCE(last_error,'')='' ").fetchone()[0]
    con.close()
    manifests = len(list(DB.render_root.glob("*/render_manifest.json")))
    queue_path = DB.thumbnail_job_root / "queue.json"
    return {
        "detail_count": total,
        "full_preview_count": full,
        "layout_file_count": files,
        "render_manifest_count": manifests,
        "queue_exists": queue_path.exists(),
        "queue_path": str(queue_path),
        "hidden_layers": thumbnail_hidden_layers(),
    }


def prepare_thumbnail_queue(hidden_layers: Optional[Sequence[str]] = None) -> dict:
    if hidden_layers is not None:
        hidden = save_thumbnail_hidden_layers(hidden_layers)
    else:
        hidden = thumbnail_hidden_layers()

    con = DB.connect()
    rows = con.execute(
        "SELECT layout_file,layout_filename,size_bytes,mtime_ns,page_count,detail_count "
        "FROM layout_files WHERE detail_count>0 AND COALESCE(last_error,'')='' ORDER BY layout_filename"
    ).fetchall()
    con.close()

    jobs = []
    for row in rows:
        source = row["layout_file"]
        key = path_key(source)
        out_dir = DB.render_root / key
        jobs.append({
            "source_layout": source,
            "layout_filename": row["layout_filename"],
            "source_key": key,
            "expected_size_bytes": row["size_bytes"],
            "expected_mtime_ns": row["mtime_ns"],
            "page_count": row["page_count"],
            "detail_count": row["detail_count"],
            "output_dir": str(out_dir),
        })

    payload = {
        "poc": "07",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "hidden_layers_exact": hidden,
        "jobs": jobs,
    }
    queue = DB.thumbnail_job_root / "queue.json"
    queue.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log_info(f"Thumbnail render queue prepared: {len(jobs)} master(s); hidden layers: {', '.join(hidden)}")
    return {"queue_path": str(queue), "job_count": len(jobs), "hidden_layers": hidden}


def process_thumbnail_renders(
    dpi: int = 220,
    margin_left: float = 0.025,
    margin_right: float = 0.025,
    margin_top: float = 0.010,
    margin_bottom: float = 0.025,
) -> dict:
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is not installed. Run the Prototype 0.1 BAT file again so it can install pymupdf.") from exc

    manifests = sorted(DB.render_root.glob("*/render_manifest.json"))
    if not manifests:
        raise RuntimeError("No rendered PDF manifests were found. Prepare the queue, then run thumbnail_worker.rb in SketchUp first.")

    con = DB.connect()
    processed_files = 0
    processed_details = 0
    skipped_files = []
    warnings = []

    for manifest_path in manifests:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            source = manifest.get("source_layout", "")
            pdf_path = Path(manifest.get("pdf", ""))
            row = con.execute("SELECT * FROM layout_files WHERE layout_file=?", (source,)).fetchone()
            if not row:
                skipped_files.append(f"Not indexed: {source}")
                continue
            if int(manifest.get("expected_size_bytes", -1)) != int(row["size_bytes"] or -2) or int(manifest.get("expected_mtime_ns", -1)) != int(row["mtime_ns"] or -2):
                skipped_files.append(f"Source changed since render queue: {row['layout_filename']}")
                continue
            if not pdf_path.is_file():
                skipped_files.append(f"Rendered PDF missing: {row['layout_filename']}")
                continue

            page_w = float(manifest["page_width_inches"])
            page_h = float(manifest["page_height_inches"])
            output_dir = DB.full_preview_root / path_key(source)
            shutil.rmtree(output_dir, ignore_errors=True)
            output_dir.mkdir(parents=True, exist_ok=True)

            doc = fitz.open(str(pdf_path))
            details = con.execute(
                "SELECT detail_key,page_index,bounds_json FROM details WHERE layout_file=? ORDER BY page_index,group_index",
                (source,),
            ).fetchall()

            file_count = 0
            for detail in details:
                bounds = json.loads(detail["bounds_json"] or "null")
                if not bounds or len(bounds) != 4:
                    warnings.append(f"No bounds: {detail['detail_key']}")
                    continue
                page_index = int(detail["page_index"] or 0)
                if page_index < 1 or page_index > len(doc):
                    warnings.append(f"Bad PDF page index {page_index}: {detail['detail_key']}")
                    continue

                x1, y1, x2, y2 = map(float, bounds)
                # Prototype 0.1: crop very tightly to the actual grouped detail.
                # Visual breathing room is added by the UI, not by capturing
                # neighboring page content.
                x1 = max(0.0, x1 - margin_left)
                y1 = max(0.0, y1 - margin_top)
                x2 = min(page_w, x2 + margin_right)
                y2 = min(page_h, y2 + margin_bottom)
                if x2 <= x1 or y2 <= y1:
                    continue

                page = doc[page_index - 1]
                sx = page.rect.width / page_w
                sy = page.rect.height / page_h
                clip = fitz.Rect(x1 * sx, y1 * sy, x2 * sx, y2 * sy)
                matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
                pix = page.get_pixmap(matrix=matrix, clip=clip, alpha=False)

                filename = hashlib.sha1(detail["detail_key"].encode("utf-8", errors="surrogatepass")).hexdigest()[:20] + ".png"
                out_path = output_dir / filename
                pix.save(str(out_path))
                rel = str(out_path.relative_to(DB.full_preview_root)).replace(os.sep, "/")
                con.execute("UPDATE details SET full_preview_relpath=? WHERE detail_key=?", (rel, detail["detail_key"]))
                file_count += 1
                processed_details += 1

            doc.close()
            con.commit()
            processed_files += 1
            matched = manifest.get("hidden_layers_matched", [])
            requested = manifest.get("hidden_layers_requested", [])
            missing = [x for x in requested if x.lower() not in {str(m).lower() for m in matched}]
            if missing:
                warnings.append(f"{row['layout_filename']}: hidden layer(s) not found: {', '.join(missing)}")
        except Exception as exc:
            con.rollback()
            skipped_files.append(f"{manifest_path.name}: {type(exc).__name__}: {exc}")

    con.close()
    log_info(f"Thumbnails processed: {processed_details} detail(s) from {processed_files} master(s); {len(skipped_files)} skipped, {len(warnings)} warning(s)")
    for item in skipped_files: log_warning(f"Thumbnail skipped: {item}")
    for item in warnings: log_warning(f"Thumbnail warning: {item}")
    return {
        "processed_files": processed_files,
        "processed_details": processed_details,
        "skipped_files": skipped_files,
        "warnings": warnings,
        "dpi": dpi,
        "margins_inches": {
            "left": margin_left,
            "right": margin_right,
            "top": margin_top,
            "bottom": margin_bottom,
        },
    }


def diagnostics(max_lines: int = 300) -> dict:
    """Everything the Diagnostics panel shows. Read-only."""
    cfg = DB.get_config(); library_root = cfg.get("library_root", "")
    con = DB.connect()
    masters = con.execute("SELECT COUNT(*) FROM layout_files").fetchone()[0]
    details = con.execute("SELECT COUNT(*) FROM details").fetchone()[0]
    full = con.execute("SELECT COUNT(*) FROM details WHERE COALESCE(full_preview_relpath,'')<>''").fetchone()[0]
    last_indexed = con.execute("SELECT MAX(last_indexed_utc) FROM layout_files").fetchone()[0] or ""
    failed = [dict(r) for r in con.execute("SELECT layout_filename,layout_file,last_error,last_indexed_utc FROM layout_files WHERE COALESCE(last_error,'')<>'' ORDER BY layout_filename")]
    con.close()
    worker = None
    worker_path = DB.thumbnail_job_root / "last_worker_result.json"
    if worker_path.exists():
        try:
            raw = json.loads(worker_path.read_text(encoding="utf-8"))
            worker = {"completed_at": str(raw.get("completed_at", "")), "successes": int(raw.get("successes", 0) or 0), "failures": [{"file": str(f.get("file", "")), "error": str(f.get("error", ""))} for f in (raw.get("failures") or []) if isinstance(f, dict)]}
        except Exception as exc:
            worker = {"completed_at": "", "successes": 0, "failures": [{"file": str(worker_path), "error": f"Could not read worker result: {type(exc).__name__}: {exc}"}]}
    try: reachable = bool(library_root) and Path(library_root).is_dir()
    except Exception: reachable = False
    log = read_log_tail(max_lines)
    return {
        "app": APP_NAME, "python": sys.version.split()[0], "data_dir": str(DB.root),
        "log_path": str(LOG_PATH) if LOG_PATH else "", "log_setup_error": LOG_SETUP_ERROR,
        "library_root": library_root, "library_reachable": reachable,
        "master_count": masters, "detail_count": details, "full_preview_count": full, "last_indexed_utc": last_indexed,
        "failed_masters": failed, "worker": worker, "log": log,
        "problem_count": len(failed) + (len(worker["failures"]) if worker else 0) + (0 if reachable or not library_root else 1) + (1 if LOG_SETUP_ERROR else 0),
    }


INDEX_HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Detail Manager Prototype 0.1</title>
<style>
:root{--card-w:420px;--bg:#f4f5f7;--panel:#fff;--border:#d7dbe0;--text:#20242a;--muted:#67717e;--accent:#315b86;--shadow:0 2px 10px rgba(0,0,0,.08)}*{box-sizing:border-box}body{margin:0;font:14px/1.35 "Segoe UI",Arial,sans-serif;background:var(--bg);color:var(--text);height:100vh;overflow:hidden}header{height:74px;background:#fff;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:16px;padding:12px 18px}.brand{font-weight:700;font-size:19px;white-space:nowrap}.search{flex:1;min-width:280px;height:42px;border:1px solid #aeb6c0;border-radius:7px;padding:0 14px;font-size:17px}button{border:1px solid #aab2bc;background:#fff;border-radius:6px;padding:8px 12px;cursor:pointer;font-weight:600}button:hover{background:#f2f5f8}button.primary{background:var(--accent);color:#fff;border-color:var(--accent)}.sizebox{display:flex;align-items:center;gap:8px;white-space:nowrap;color:var(--muted)}.app{display:grid;grid-template-columns:285px 1fr;height:calc(100vh - 74px)}aside{background:#fff;border-right:1px solid var(--border);overflow:auto;padding:14px}.aside-title{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:5px 0 8px}.pathbox{font-size:12px;word-break:break-all;background:#f8f9fb;border:1px solid var(--border);border-radius:5px;padding:8px;margin-bottom:8px}.source,.cat{display:block;width:100%;text-align:left;border:0;border-radius:4px;padding:7px 8px;font-weight:400}.source.active,.cat.active{background:#e8eef5;font-weight:600}.cat{font-size:14px}.cat.sub{padding-left:24px;font-size:13px;color:#3d4753}.source{font-size:12px}.adv{margin-top:14px;border-top:1px solid var(--border);padding-top:10px}.adv>summary{cursor:pointer;font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:8px}.adv[open]>summary{margin-bottom:10px}#filterlabel{color:var(--text);font-weight:600}.count{float:right;color:var(--muted)}.thumbtools{border:1px solid var(--border);border-radius:7px;padding:10px;background:#f8f9fb}.thumbtools input[type=text]{width:100%;padding:7px 8px;border:1px solid #b9c0c8;border-radius:5px;margin:4px 0 8px}.thumbtools button{width:100%;margin-top:6px}.smallnote{font-size:11px;color:var(--muted);margin-top:7px}.thumbstatus{font-size:12px;margin:7px 0;color:#45515e}main{overflow:auto;padding:16px 18px 50px}.statusline{display:flex;gap:16px;align-items:center;color:var(--muted);margin:0 0 13px}.notice{background:#edf4fb;border:1px solid #b8cee3;border-radius:6px;padding:8px 10px;color:#2f4d69}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(var(--card-w),100%),1fr));gap:16px;align-items:start}.card{background:var(--panel);border:1px solid var(--border);border-radius:8px;box-shadow:var(--shadow);overflow:hidden;min-width:0}.thumb{height:calc(var(--card-w)*.72);min-height:250px;max-height:485px;background:#e9ebee;display:grid;grid-template-columns:1fr;grid-auto-rows:minmax(0,1fr);gap:2px;align-items:stretch;justify-content:stretch;overflow:hidden;cursor:pointer;position:relative}.thumb.fallback.count-2,.thumb.fallback.count-3,.thumb.fallback.count-4{grid-template-columns:repeat(2,minmax(0,1fr))}.thumb.fallback.count-5,.thumb.fallback.count-6{grid-template-columns:repeat(3,minmax(0,1fr))}.thumb img{width:100%;height:100%;min-width:0;min-height:0;object-fit:contain;background:white}.thumb.full{background:white;padding:10px}.thumb.full img{max-width:100%;max-height:100%}.previewbadge{position:absolute;right:7px;bottom:7px;background:rgba(30,36,43,.78);color:#fff;border-radius:4px;padding:3px 6px;font-size:10px;pointer-events:none}.meta{padding:11px 12px}.title{font-size:16px;font-weight:700;margin:0 0 4px}.rawtitle{color:#4e5966;font-size:12px;margin-bottom:4px}.mastertitle{color:var(--muted);font-size:12px;margin-bottom:3px}.sub{color:var(--muted);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.actions{display:flex;gap:7px;margin-top:10px;flex-wrap:wrap}.actions button{padding:6px 9px;font-size:12px}.empty{padding:50px;text-align:center;color:var(--muted);font-size:17px}#progress{height:4px;background:#e2e6eb;position:fixed;left:285px;right:0;top:74px;z-index:10;display:none}#progress>div{height:100%;background:var(--accent);width:0}.modalback{position:fixed;inset:0;background:rgba(0,0,0,.42);display:none;align-items:center;justify-content:center;z-index:50;padding:25px}.modal{width:min(1600px,97vw);height:min(960px,95vh);background:#fff;border-radius:9px;box-shadow:0 15px 50px rgba(0,0,0,.3);display:grid;grid-template-columns:minmax(720px,1.8fr) minmax(370px,.62fr);overflow:hidden}.modalview{background:#eceff2;padding:16px;overflow:auto;display:flex;align-items:center;justify-content:center}.modalimgs{display:grid;grid-template-columns:1fr;grid-auto-rows:minmax(280px,1fr);gap:8px;width:100%;height:100%}.modalimgs.fallback.count-2,.modalimgs.fallback.count-3,.modalimgs.fallback.count-4{grid-template-columns:repeat(2,minmax(0,1fr))}.modalimgs.fallback.count-5,.modalimgs.fallback.count-6{grid-template-columns:repeat(3,minmax(0,1fr))}.modalimgs img{width:100%;height:100%;min-width:0;min-height:280px;object-fit:contain;background:white;border:1px solid #c8cdd3}.modalimgs.full{background:white;padding:14px}.modalinfo{padding:18px;overflow:auto;position:relative}.close{position:absolute;right:12px;top:10px;font-size:22px;border:0}.modalinfo h2{padding-right:35px;margin-top:3px;margin-bottom:3px}.detailtext{white-space:pre-wrap;background:#f7f8fa;border:1px solid var(--border);padding:10px;border-radius:5px;max-height:300px;overflow:auto;font-size:12px}.kv{margin:8px 0}.kv b{display:block;font-size:11px;text-transform:uppercase;color:var(--muted);letter-spacing:.05em}.badge{display:inline-block;min-width:18px;padding:1px 6px;border-radius:9px;background:#b3261e;color:#fff;font-size:11px;margin-left:6px}.diag{width:min(1100px,95vw);height:min(820px,92vh);background:#fff;border-radius:9px;box-shadow:0 15px 50px rgba(0,0,0,.3);padding:18px;overflow:auto;position:relative}.diag h2{margin:2px 0 10px}.diag h3{margin:16px 0 6px;font-size:14px}.diag table{border-collapse:collapse;width:100%;font-size:12px}.diag td,.diag th{border-bottom:1px solid var(--border);padding:4px 6px;text-align:left;vertical-align:top}.diag .ok{color:#1e6b34}.diag .bad{color:#b3261e;font-weight:600}.diag .lvl-ERROR td{color:#b3261e}.diag .lvl-WARNING td{color:#8a5a00}.diag .path{word-break:break-all}.toast{position:fixed;right:24px;bottom:24px;background:#20242a;color:#fff;padding:12px 16px;border-radius:7px;display:none;max-width:680px;z-index:80;box-shadow:var(--shadow)}@media(max-width:1100px){.app{grid-template-columns:230px 1fr}#progress{left:230px}.modal{grid-template-columns:1fr}.modalinfo{display:none}}
</style></head><body>
<header><div class="brand">Detail Manager <span style="font-weight:400;color:#788391">Prototype 0.1</span></div><input id="search" class="search" placeholder="Search: floor, FLR, retaining wall, RET, I-joist, TJI..." autofocus><div class="sizebox"><span>Thumbnail</span><input id="size" type="range" min="320" max="640" value="420" step="20"><span id="sizeval">420</span></div><button id="refresh">Refresh Index</button></header><div id="progress"><div></div></div>
<div class="app"><aside><div class="aside-title">Categories</div><button class="cat active" data-cat="">All Details <span id="allcount" class="count"></span></button><div id="cats"></div><details class="adv"><summary>Source files (advanced)</summary><div id="sources"></div></details><details class="adv"><summary>Library and admin tools</summary><div class="aside-title">Library</div><div id="libpath" class="pathbox">No library selected</div><button id="choose" style="width:100%;margin-bottom:12px">Choose Library Folder</button><div class="aside-title" style="margin-top:12px">Full Thumbnails</div><div class="thumbtools"><label style="font-size:11px;color:#67717e">Hide exact LayOut layer name(s)</label><input id="hiddenlayers" type="text" value="GUIDES" title="Comma-separated exact layer names"><div id="thumbstatus" class="thumbstatus"></div><div class="smallnote"><b>07A:</b> Tight crop uses 0.01&quot; top and 0.025&quot; left/right/bottom margins; white padding is added in the card instead of capturing adjacent page content.</div><button id="preparethumbs" class="primary">1. Prepare Render Queue</button><div class="smallnote">2. In SketchUp Ruby Console, load <b>thumbnail_worker.rb</b>. It renders the queued masters read-only with these layers hidden.</div><button id="processthumbs">3. Process Rendered Thumbnails</button></div><div class="aside-title" style="margin-top:18px">Temp</div><button id="cleanup" style="width:100%">Clean Staging Files</button></details><button id="diagbtn" style="width:100%;margin-top:14px">Diagnostics<span id="diagbadge" class="badge" style="display:none"></span></button></aside>
<main><div class="statusline"><span id="resultcount"></span><span id="filterlabel"></span><span id="indexstatus"></span></div><div id="grid" class="grid"></div></main></div>
<div id="modalback" class="modalback"><div class="modal"><div class="modalview"><div id="modalimgs" class="modalimgs"></div></div><div class="modalinfo"><button id="close" class="close">×</button><h2 id="modaltitle"></h2><div id="modalraw" class="rawtitle"></div><div id="modalmeta"></div><h3>Notes on the detail</h3><div id="modaltext" class="detailtext"></div><details style="margin-top:8px"><summary style="cursor:pointer;color:var(--muted);font-size:12px">Everything read from the LayOut file (raw)</summary><div id="modalrawtext" class="detailtext" style="margin-top:6px"></div></details><div class="actions" style="margin-top:14px"><button id="modalopen" class="primary">Open Detail</button><button id="modalmaster">Open Master LayOut</button><button id="modalskp">Open SketchUp Source</button></div></div></div></div><div id="diagback" class="modalback"><div class="diag"><button id="diagclose" class="close">×</button><h2>Diagnostics</h2><div id="diagbody"></div></div></div><div id="toast" class="toast"></div>
<script>
let currentSource='',currentCat='',currentDetails=[],modalDetail=null,timer=null;const q=s=>document.querySelector(s),grid=q('#grid');function esc(s){return (s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}async function api(url,opt){const r=await fetch(url,opt),j=await r.json();if(!r.ok)throw new Error(j.error||r.statusText);return j}function toast(msg){const t=q('#toast');t.textContent=msg;t.style.display='block';setTimeout(()=>t.style.display='none',8500)}function vclass(d){return 'count-'+Math.min(Math.max(d.viewports.length,1),6)}
function thumbHtml(d,modal=false){if(d.full_preview_relpath){return `<img loading="lazy" src="/fullcache/${encodeURI(d.full_preview_relpath)}" title="Full LayOut detail"><span class="previewbadge">Full LayOut Preview</span>`}if(!d.viewports.length)return '<div style="color:#777">No preview</div>';let imgs=d.viewports.slice(0,6).map(v=>v.preview_relpath?`<img loading="lazy" src="/cache/${encodeURI(v.preview_relpath)}" title="${esc(v.scene_name)}">`:'').join('');return imgs+`<span class="previewbadge">Viewport Cache</span>`}
function render(){q('#resultcount').textContent=`${currentDetails.length} result${currentDetails.length==1?'':'s'}`;grid.innerHTML='';if(!currentDetails.length){grid.innerHTML='<div class="empty">No details found.</div>';return}currentDetails.forEach(d=>{let c=document.createElement('article');c.className='card';let full=!!d.full_preview_relpath;c.innerHTML=`<div class="thumb ${full?'full':'fallback '+vclass(d)}">${thumbHtml(d)}</div><div class="meta"><div class="title">${esc(d.expanded_title||d.display_title)}</div>${d.scene_label?`<div class="rawtitle">${esc(d.scene_label)}</div>`:''}<div class="mastertitle">${esc(d.master_title||'')}</div><div class="sub">${esc(d.layout_filename)} · ${esc(d.page_name)} · ${d.viewport_count} viewport${d.viewport_count==1?'':'s'}</div><div class="actions"><button class="od primary">Open Detail</button><button class="om">Master</button><button class="info">Preview</button></div></div>`;c.querySelector('.thumb').onclick=()=>openModal(d);c.querySelector('.info').onclick=()=>openModal(d);c.querySelector('.od').onclick=e=>{e.stopPropagation();openDetail(d)};c.querySelector('.om').onclick=e=>{e.stopPropagation();openMaster(d)};grid.appendChild(c)})}
async function search(){try{let j=await api(`/api/search?q=${encodeURIComponent(q('#search').value)}&source=${encodeURIComponent(currentSource)}&category=${encodeURIComponent(currentCat)}`);currentDetails=j.details;render()}catch(e){toast(e.message)}}
function setFilter(cat,src,btn,label){currentCat=cat;currentSource=src;document.querySelectorAll('.source,.cat').forEach(x=>x.classList.remove('active'));if(btn)btn.classList.add('active');q('#filterlabel').textContent=label?'in '+label:'';search()}
function mkCat(cls,label,count,key,full){let b=document.createElement('button');b.className=cls;b.dataset.cat=key;b.innerHTML=`${esc(label)} <span class="count">${count}</span>`;if(currentCat===key)b.classList.add('active');b.onclick=()=>setFilter(key,'',b,full);return b}
async function loadSources(){let j=await api('/api/status');q('#libpath').textContent=j.library_root||'No library selected';q('#sources').innerHTML='';q('#cats').innerHTML='';let total=0;j.sources.forEach(s=>{total+=s.detail_count||0;let b=document.createElement('button');b.className='source';b.innerHTML=`${esc(s.layout_filename)} <span class="count">${s.detail_count||0}</span>`;b.title=s.layout_file;if(currentSource===s.layout_file)b.classList.add('active');b.onclick=()=>setFilter('',s.layout_file,b,s.layout_filename);q('#sources').appendChild(b)});(j.categories||[]).forEach(g=>{q('#cats').appendChild(mkCat('cat',g.name,g.count,g.key,g.name));(g.children||[]).forEach(c=>q('#cats').appendChild(mkCat('cat sub',c.sub,c.count,c.key,g.name+' › '+c.sub)))});q('#allcount').textContent=total;let all=q('.cat[data-cat=""]');all.onclick=()=>setFilter('','',all,'');if(!currentCat&&!currentSource)all.classList.add('active');await loadThumbStatus()}
async function loadThumbStatus(){try{let s=await api('/api/thumbnail-status');q('#hiddenlayers').value=(s.hidden_layers||['GUIDES']).join(', ');q('#thumbstatus').textContent=`${s.full_preview_count}/${s.detail_count} full previews · ${s.render_manifest_count} rendered master${s.render_manifest_count==1?'':'s'} ready`;}catch(e){}}
async function choose(){try{let j=await api('/api/choose-library',{method:'POST'});if(j.library_root){q('#libpath').textContent=j.library_root;startIndex(j.library_root)}}catch(e){toast(e.message)}}async function startIndex(root){try{await api('/api/index',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({library_root:root})});pollIndex()}catch(e){toast(e.message)}}async function pollIndex(){let j=await api('/api/index-status'),p=q('#progress'),bar=p.firstElementChild;if(j.running){p.style.display='block';bar.style.width=(j.total?100*j.done/j.total:2)+'%';q('#indexstatus').textContent=`Indexing ${j.done}/${j.total}: ${j.current||j.message}`;setTimeout(pollIndex,500)}else{p.style.display='none';q('#indexstatus').textContent=j.message||'';await loadSources();await search();if(j.errors?.length)toast(`${j.errors.length} file(s) had indexing errors. Open Diagnostics (bottom of the left panel) for the list.`);loadDiagBadge()}}
async function openDetail(d){try{await api('/api/open-detail',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({detail_key:d.detail_key})});toast(`Opened lightweight staging detail (${d.viewport_count} viewport${d.viewport_count==1?'':'s'}). Copy it normally, close staging, then paste into your project.`)}catch(e){toast(e.message)}}async function openMaster(d){try{await api('/api/open-master',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({detail_key:d.detail_key})})}catch(e){toast(e.message)}}async function openSkp(d){try{await api('/api/open-skp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({detail_key:d.detail_key})})}catch(e){toast(e.message)}}
function openModal(d){modalDetail=d;q('#modaltitle').textContent=d.expanded_title||d.display_title;q('#modalraw').textContent=d.scene_label||'';let full=!!d.full_preview_relpath;q('#modalimgs').className='modalimgs '+(full?'full':'fallback '+vclass(d));q('#modalimgs').innerHTML=thumbHtml(d,true);let paths=d.skp_paths_exact||[];q('#modalmeta').innerHTML=`<div class="kv"><b>Intended Master Title</b>${esc(d.master_title||'')}</div><div class="kv"><b>Source LayOut</b>${esc(d.layout_filename)}</div><div class="kv"><b>Page</b>${esc(d.page_name)}</div><div class="kv"><b>Scene(s)</b>${d.viewports.map(v=>esc(v.scene_name)).join('<br>')}</div><div class="kv"><b>SketchUp reference path</b>${paths.map(esc).join('<br>')}</div>`;q('#modaltext').textContent=d.clean_text?(d.notes_text||'(no notes)'):(d.searchable_text||'');q('#modalrawtext').textContent=d.raw_text||'(refresh the index to see the raw text)';q('#modalback').style.display='flex'}q('#close').onclick=()=>q('#modalback').style.display='none';q('#modalback').onclick=e=>{if(e.target===q('#modalback'))q('#modalback').style.display='none'};q('#modalopen').onclick=()=>modalDetail&&openDetail(modalDetail);q('#modalmaster').onclick=()=>modalDetail&&openMaster(modalDetail);q('#modalskp').onclick=()=>modalDetail&&openSkp(modalDetail);
q('#search').oninput=()=>{clearTimeout(timer);timer=setTimeout(search,180)};q('#size').oninput=e=>{let v=e.target.value;document.documentElement.style.setProperty('--card-w',v+'px');q('#sizeval').textContent=v};q('#choose').onclick=choose;q('#refresh').onclick=async()=>{let j=await api('/api/status');j.library_root?startIndex(j.library_root):choose()};q('#cleanup').onclick=async()=>{let j=await api('/api/cleanup',{method:'POST'});toast(`Deleted ${j.deleted} staging file(s).`)};
q('#preparethumbs').onclick=async()=>{try{let hidden=q('#hiddenlayers').value.split(',').map(x=>x.trim()).filter(Boolean);let j=await api('/api/prepare-thumbnails',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({hidden_layers:hidden})});toast(`Prepared ${j.job_count} master file(s). Now load thumbnail_worker.rb in the SketchUp Ruby Console.`);await loadThumbStatus()}catch(e){toast(e.message)}};
q('#processthumbs').onclick=async()=>{try{q('#indexstatus').textContent='Processing full-detail thumbnails...';let j=await api('/api/process-thumbnails',{method:'POST'});let probs=(j.warnings?.length||0)+(j.skipped_files?.length||0);toast(`Created/updated ${j.processed_details} full previews from ${j.processed_files} master file(s).${probs?' '+probs+' warning(s) or skipped file(s) - see Diagnostics.':''}`);loadDiagBadge();await loadThumbStatus();await search();q('#indexstatus').textContent='Full thumbnails processed';}catch(e){toast(e.message);q('#indexstatus').textContent=''}};
async function loadDiagBadge(){try{let d=await api('/api/diagnostics');let b=q('#diagbadge');b.textContent=d.problem_count;b.style.display=d.problem_count?'inline-block':'none';return d}catch(e){return null}}
function diagRows(rows){return rows.map(r=>`<tr><th style="width:190px">${esc(r[0])}</th><td class="path">${r[1]}</td></tr>`).join('')}
async function openDiag(){let d=await loadDiagBadge();if(!d){toast('Diagnostics could not be loaded.');return}let probsOnly=q('#diagprob')?q('#diagprob').checked:true;let log=(d.log||[]).filter(x=>!probsOnly||x.level!=='INFO').slice(-150).reverse();let h=`<table>${diagRows([['Program',esc(d.app)+' (Python '+esc(d.python)+')'],['Library folder',esc(d.library_root||'none chosen')+(d.library_root?(d.library_reachable?' <span class="ok">reachable</span>':' <span class="bad">NOT reachable - check the drive</span>'):'')],['Indexed',`${d.master_count} master file(s), ${d.detail_count} detail(s), ${d.full_preview_count} full thumbnail(s)`],['Last index (UTC)',esc(d.last_indexed_utc||'never')],['Data folder',esc(d.data_dir)],['Log file',d.log_path?esc(d.log_path):'<span class="bad">not available: '+esc(d.log_setup_error)+'</span>']])}</table><div class="actions"><button id="diagopen">Open Log Folder</button><button id="diagrefresh">Refresh</button></div>`;
h+=`<h3>Master files that could not be indexed (${d.failed_masters.length})</h3>`+(d.failed_masters.length?`<table>${d.failed_masters.map(f=>`<tr><td title="${esc(f.layout_file)}">${esc(f.layout_filename)}</td><td class="bad">${esc(f.last_error)}</td></tr>`).join('')}</table>`:'<div class="ok">None.</div>');
h+=`<h3>Last thumbnail render in SketchUp</h3>`+(d.worker?`<div>${esc(d.worker.completed_at)}: ${d.worker.successes} rendered, ${d.worker.failures.length} failed</div>`+(d.worker.failures.length?`<table>${d.worker.failures.map(f=>`<tr><td class="path">${esc(f.file)}</td><td class="bad">${esc(f.error)}</td></tr>`).join('')}</table>`:''):'<div>No render has been run from this data folder yet.</div>');
h+=`<h3>Recent log entries <label style="font-weight:400;margin-left:10px"><input type="checkbox" id="diagprob" ${probsOnly?'checked':''}> problems only</label></h3>`+(log.length?`<table>${log.map(x=>`<tr class="lvl-${esc(x.level)}"><td style="white-space:nowrap">${esc(x.time)}</td><td>${esc(x.level)}</td><td class="path">${esc(x.message)}</td></tr>`).join('')}</table>`:`<div class="ok">${probsOnly?'No warnings or errors in the log.':'The log is empty.'}</div>`);
q('#diagbody').innerHTML=h;q('#diagback').style.display='flex';q('#diagprob').onchange=openDiag;q('#diagrefresh').onclick=openDiag;q('#diagopen').onclick=async()=>{try{await api('/api/open-log-folder',{method:'POST'})}catch(e){toast(e.message)}}}
q('#diagbtn').onclick=openDiag;q('#diagclose').onclick=()=>q('#diagback').style.display='none';q('#diagback').onclick=e=>{if(e.target===q('#diagback'))q('#diagback').style.display='none'};
(async()=>{loadDiagBadge();await loadSources();let s=await api('/api/index-status');s.running?pollIndex():search()})();
</script></body></html>
'''

class Handler(BaseHTTPRequestHandler):
    server_version = "DetailManagerPOC07A/0.71"
    def log_message(self, fmt, *args): return
    def send_json(self, obj, status=200):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8"); self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def read_json(self):
        n = int(self.headers.get("Content-Length", "0") or 0); return json.loads(self.rfile.read(n) or b"{}")
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/":
            b = INDEX_HTML.encode("utf-8"); self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
        if u.path == "/api/status": self.send_json({"library_root": DB.get_config().get("library_root", ""), "sources": library_sources(), "categories": library_categories()}); return
        if u.path == "/api/thumbnail-status": self.send_json(thumbnail_status()); return
        if u.path == "/api/diagnostics": self.send_json(diagnostics()); return
        if u.path == "/api/index-status":
            with INDEX_LOCK: state = dict(INDEX_STATE)
            self.send_json(state); return
        if u.path == "/api/search":
            qs = urllib.parse.parse_qs(u.query); self.send_json({"details": search_details(qs.get("q", [""])[0], qs.get("source", [""])[0], category=qs.get("category", [""])[0])}); return
        if u.path.startswith("/cache/"):
            rel = urllib.parse.unquote(u.path[len("/cache/"):]); p = DB.preview_root / rel
            try:
                rp, base = p.resolve(), DB.preview_root.resolve()
                if base not in rp.parents and rp != base: raise ValueError
                data = rp.read_bytes(); mime = mimetypes.guess_type(str(rp))[0] or "application/octet-stream"; self.send_response(200); self.send_header("Content-Type", mime); self.send_header("Cache-Control", "public,max-age=86400"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
            except Exception: self.send_error(404)
            return
        if u.path.startswith("/fullcache/"):
            rel = urllib.parse.unquote(u.path[len("/fullcache/"):]); p = DB.full_preview_root / rel
            try:
                rp, base = p.resolve(), DB.full_preview_root.resolve()
                if base not in rp.parents and rp != base: raise ValueError
                data = rp.read_bytes(); mime = mimetypes.guess_type(str(rp))[0] or "image/png"; self.send_response(200); self.send_header("Content-Type", mime); self.send_header("Cache-Control", "public,max-age=86400"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
            except Exception: self.send_error(404)
            return
        self.send_error(404)
    def do_POST(self):
        try:
            u = urllib.parse.urlparse(self.path)
            if u.path == "/api/choose-library":
                import tkinter as tk
                from tkinter import filedialog
                r = tk.Tk(); r.withdraw(); r.attributes('-topmost', True); folder = filedialog.askdirectory(title="Choose LayOut Detail Library Folder"); r.destroy(); self.send_json({"library_root": folder or ""}); return
            if u.path == "/api/index":
                root = self.read_json().get("library_root", "")
                if not root or not Path(root).is_dir(): raise ValueError("Choose a valid library folder")
                with INDEX_LOCK:
                    if INDEX_STATE["running"]: raise ValueError("Index refresh is already running")
                threading.Thread(target=index_library, args=(root,), daemon=True).start(); self.send_json({"started": True}); return
            if u.path == "/api/prepare-thumbnails":
                payload = self.read_json()
                hidden = payload.get("hidden_layers", thumbnail_hidden_layers())
                if isinstance(hidden, str): hidden = [x.strip() for x in hidden.split(",") if x.strip()]
                self.send_json(prepare_thumbnail_queue(hidden)); return
            if u.path == "/api/process-thumbnails":
                self.send_json(process_thumbnail_renders()); return
            if u.path in {"/api/open-detail", "/api/open-master", "/api/open-skp"}:
                key = self.read_json().get("detail_key", ""); con = DB.connect(); d = con.execute("SELECT * FROM details WHERE detail_key=?", (key,)).fetchone(); con.close()
                if not d: raise ValueError("Detail not found")
                if u.path == "/api/open-detail":
                    out = build_staging(key); windows_open(str(out)); log_info(f"Open Detail: {d['layout_filename']} / {d['display_title']} -> {out.name}"); self.send_json({"opened": True, "staging_file": str(out)}); return
                if u.path == "/api/open-master": windows_open(d["layout_file"]); self.send_json({"opened": True}); return
                paths = json.loads(d["skp_paths_exact"] or "[]")
                if not paths: raise ValueError("No SketchUp reference path was indexed")
                windows_open(paths[0]); self.send_json({"opened": True, "path": paths[0]}); return
            if u.path == "/api/open-log-folder":
                if not LOG_PATH: raise ValueError("The log file could not be created: " + LOG_SETUP_ERROR)
                windows_open(str(LOG_PATH.parent)); self.send_json({"opened": True, "folder": str(LOG_PATH.parent)}); return
            if u.path == "/api/cleanup":
                deleted = 0
                for p in DB.staging_root.glob("*.layout"):
                    try: p.unlink(); deleted += 1
                    except Exception: pass
                self.send_json({"deleted": deleted}); return
            self.send_error(404)
        except Exception as exc:
            log_error(f"{urllib.parse.urlparse(self.path).path} failed: {type(exc).__name__}: {exc}")
            self.send_json({"error": f"{type(exc).__name__}: {exc}"}, status=400)


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=PORT_DEFAULT); ap.add_argument("--library", default=""); ap.add_argument("--no-browser", action="store_true"); args = ap.parse_args(argv)
    log_info(f"{APP_NAME} started (Python {sys.version.split()[0]}, port {args.port}, data: {DB.root})")
    removed = cleanup_staging(24)
    if removed: log_info(f"Startup cleanup: deleted {removed} staging file(s) older than 24 hours")
    if args.library:
        DB.save_config({"library_root": args.library}); threading.Thread(target=index_library, args=(args.library,), daemon=True).start()
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError as exc:
        msg = f"Could not start: port {args.port} is already in use. Detail Manager (or an older copy of it) is probably already running - close that window first. ({exc})"
        print(msg); log_error(msg); return 1
    url = f"http://127.0.0.1:{args.port}/"; print(f"{APP_NAME} running at {url}"); print(f"Local data: {DB.root}"); print(f"Log file: {LOG_PATH or 'not available - ' + LOG_SETUP_ERROR}"); print("Close this console window or press Ctrl+C to stop.")
    if not args.no_browser: threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__ == "__main__": raise SystemExit(main())
