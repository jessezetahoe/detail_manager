"""Write approved parser snapshots: python tests/make_golden.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import GOLDEN, fixture_files, parse  # noqa: E402
from golden_snapshot import snapshot  # noqa: E402

GOLDEN.mkdir(exist_ok=True)
for p in fixture_files():
    out = GOLDEN / (p.stem + ".json")
    out.write_text(json.dumps(snapshot(*parse(p)), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", out.name)
