"""Clipboard probe (Windows only, read-only).

Purpose: find out what LayOut puts on the Windows clipboard when a detail is
copied, so we can tell whether Detail Manager could place a detail on the
clipboard itself (then the user would only press Ctrl+V in the project).

How to use:
  1. In LayOut, open any detail and copy it (Ctrl+C) the normal way.
  2. Run:  py tools\\clipboard_probe.py
  3. Tell Claude it ran. The results are written to
       tests\\fixtures\\clipboard_probe\\<date-time>\\
     (that folder is never put on GitHub).

The script only READS the clipboard. It does not change or clear it.
"""
import ctypes
import ctypes.wintypes as w
import datetime
import json
import os
import sys
from pathlib import Path

if os.name != "nt":
    sys.exit("This script only runs on Windows.")

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
user32.OpenClipboard.argtypes = [w.HWND]
user32.OpenClipboard.restype = w.BOOL
user32.CloseClipboard.restype = w.BOOL
user32.EnumClipboardFormats.argtypes = [w.UINT]
user32.EnumClipboardFormats.restype = w.UINT
user32.GetClipboardData.argtypes = [w.UINT]
user32.GetClipboardData.restype = w.HANDLE
user32.GetClipboardFormatNameW.argtypes = [w.UINT, w.LPWSTR, ctypes.c_int]
user32.GetClipboardFormatNameW.restype = ctypes.c_int
kernel32.GlobalLock.argtypes = [w.HGLOBAL]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [w.HGLOBAL]
kernel32.GlobalSize.argtypes = [w.HGLOBAL]
kernel32.GlobalSize.restype = ctypes.c_size_t

STANDARD = {1: "CF_TEXT", 2: "CF_BITMAP", 3: "CF_METAFILEPICT", 7: "CF_OEMTEXT", 8: "CF_DIB",
            9: "CF_PALETTE", 13: "CF_UNICODETEXT", 14: "CF_ENHMETAFILE", 15: "CF_HDROP",
            16: "CF_LOCALE", 17: "CF_DIBV5"}
NOT_MEMORY = {2, 9, 14}  # GDI handles, not readable as memory
MAX_SAVE = 200 * 1024 * 1024


def fmt_name(fmt):
    if fmt in STANDARD:
        return STANDARD[fmt]
    buf = ctypes.create_unicode_buffer(256)
    n = user32.GetClipboardFormatNameW(fmt, buf, 256)
    return buf.value if n else f"format_{fmt}"


def safe(name):
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)[:60]


def main():
    out = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "clipboard_probe" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    if not user32.OpenClipboard(None):
        sys.exit("Could not open the clipboard (another program has it open). Try again.")
    report = []
    try:
        fmt = 0
        while True:
            fmt = user32.EnumClipboardFormats(fmt)
            if not fmt:
                break
            entry = {"id": fmt, "name": fmt_name(fmt)}
            if fmt in NOT_MEMORY:
                entry["note"] = "graphics handle (not saved)"
                report.append(entry)
                continue
            h = user32.GetClipboardData(fmt)
            if not h:
                entry["note"] = "no data"
                report.append(entry)
                continue
            size = kernel32.GlobalSize(h)
            entry["bytes"] = size
            ptr = kernel32.GlobalLock(h)
            if ptr and size:
                data = ctypes.string_at(ptr, min(size, MAX_SAVE))
                kernel32.GlobalUnlock(h)
                fname = f"{fmt:05d}_{safe(entry['name'])}.bin"
                (out / fname).write_bytes(data)
                entry["saved_as"] = fname
                entry["starts_with"] = data[:64].hex(" ")
                if fmt == 15:  # file list: decode the paths
                    try:
                        offset = int.from_bytes(data[0:4], "little")
                        wide = int.from_bytes(data[16:20], "little")
                        raw = data[offset:]
                        text = raw.decode("utf-16-le" if wide else "mbcs", errors="replace")
                        entry["files"] = [x for x in text.split("\x00") if x]
                    except Exception as exc:
                        entry["files_error"] = str(exc)
            else:
                entry["note"] = "could not read"
            report.append(entry)
    finally:
        user32.CloseClipboard()
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [f"{e['id']:6d}  {e['name']:40s}  {e.get('bytes', '-'):>12}  {e.get('note', '')}" for e in report]
    (out / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nSaved to: {out}")
    print("Done. Nothing on the clipboard was changed.")


if __name__ == "__main__":
    main()
