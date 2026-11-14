# Status / resume point

**Paused:** 2026-11-14
**Branch:** `feature/regression-tests` (not yet merged to `main`)
**Source:** unchanged from Prototype 0.1 baseline (SHA-256 d52bee81...)

## Done
- Repo created; first commit = untouched handoff.
- Rules (`CLAUDE.md`), roadmap (`docs/ROADMAP.md`).
- Regression suite: 33 tests on 8 company masters / 149 details, all passing in the
  dev VM; full staging of all 149 details passes.

## Next, in order
1. **User:** run tests on Windows: `py -m unittest discover -s tests` (about 40 s).
2. If green: merge `feature/regression-tests` -> `main`.
3. New branch `feature/diagnostics-log`: persistent log in %LOCALAPPDATA% (index errors,
   thumbnail warnings), never in library/job folders.
4. 0.2 cleanup (separate branches): title fix (N.T.S. anchor across text boxes) +
   raw/clean/display metadata (drop bubble numbers, table cells, N.T.S. from clean/display);
   then slim cards + collapsed sidebar + fuller inspector; then open-to-scene.
5. Re-approve golden snapshots only for the intended title/metadata changes
   (`py tests\make_golden.py`, review `git diff tests/golden`).

## Optional input still wanted
Thumbnail render folders (`render.pdf` + `render_manifest.json`) for the 8 fixture
masters -> `tests\fixtures\renders\`, from
`%LOCALAPPDATA%\ZE Detail Manager Prototype 0.1\thumbnail_renders\`. Enables crop tests.
