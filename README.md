# Detail Manager

Search, inspect, and reuse native LayOut/SketchUp details from the company detail
library in seconds, without altering the authoritative library or its references.

- `src/` - application source (baseline: Prototype 0.1 / POC07A stable path)
- `docs/handoff/` - ChatGPT handoff (read `CLAUDE_CODE_HANDOFF.md` before changing code)
- `docs/archive/` - Prototype 0.1 deployment packages as delivered
- `tests/` - regression tests; real master files go in `tests/fixtures/` (git-ignored)

## Direction
Browser GUI was a test harness only. Target is a standalone Windows program
(see `docs/ROADMAP.md`), with a small SketchUp helper for thumbnail rendering
and open-to-scene.
