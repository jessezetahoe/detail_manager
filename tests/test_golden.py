"""Parser output must match the approved snapshot for every fixture master."""
import json
import unittest

from _support import GOLDEN, fixture_files, parse, require_fixtures
from golden_snapshot import snapshot


@require_fixtures
class TestGolden(unittest.TestCase):
    maxDiff = 4000

    def test_every_fixture_has_a_golden(self):
        missing = [p.name for p in fixture_files() if not (GOLDEN / (p.stem + ".json")).exists()]
        self.assertEqual(missing, [], "Run python tests/make_golden.py for new fixtures")

    def test_parser_matches_golden(self):
        for p in fixture_files():
            g = GOLDEN / (p.stem + ".json")
            if not g.exists():
                continue
            with self.subTest(master=p.name):
                expected = json.loads(g.read_text(encoding="utf-8"))
                actual = json.loads(json.dumps(snapshot(*parse(p)), ensure_ascii=False))
                for k in ("page_count", "detail_count", "skp_reference_count", "skp_references"):
                    self.assertEqual(actual[k], expected[k], k)
                for i, (a, e) in enumerate(zip(actual["details"], expected["details"])):
                    self.assertEqual(a, e, f"detail #{i + 1} ({e['display_title']})")


if __name__ == "__main__":
    unittest.main()
