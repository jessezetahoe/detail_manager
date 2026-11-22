# Detail Manager - rules for Claude

Read `docs/handoff/CLAUDE_CODE_HANDOFF.md` before modifying code.

## Never (regression-protected)
- Write to master `.layout` / `.skp` files during normal operations.
- Rewrite, normalize, relink, or "repair" stored SketchUp reference paths.
- Unlink/explode SketchUp references (native copy/paste consolidation depends on them).
- Split a multi-viewport detail group into separate details.
- Use AutoHotkey.
- Revive POC07C-07E crop experiments; 07A crop is the baseline.
- Re-serialize staging XML with ElementTree (use minidom, preserve namespaces).
- Write logs or sidecar files into the library or job folders. App data lives in %LOCALAPPDATA%.

## Always
- Preserve LayOut 2025 compatibility.
- Small incremental changes; tests before refactors.
- Any staging change: validate package AND have the user open it in LayOut 2025.
- Regression-check against the Z: company library (primary). The C: Distribution Library was a presentation setup; check it only when deployment changes.

## How To page (user, 2026-11-19)
- `src/how_to.html` (How To button in the program) must always match the program.
- Every change that adds, removes or changes something a user sees or does: update the
  How To in the SAME branch/commit (add, change or remove the text). Not a later task.
- Before merging a feature, check the How To still describes it correctly.

## Version number (user, 2026-11-22)
- `APP_VERSION` in `src/detail_manager.py`. Bump it on EVERY publish to the daily copy:
  last digit for fixes, middle digit for new features. Add an entry to `docs/RELEASE_HISTORY.md`.
- Tag `vX.Y.Z` on `main` once the user has verified that version.
- `tools/publish_local_release.sh` refuses to publish a different commit under a version
  that was already published.

## Git
- First commit is the untouched original; never rewrite history on `main`.
- One branch per feature (`feature/...`); merge after the user tests.
