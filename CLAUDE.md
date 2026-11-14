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
- Regression-check against both the company mapped library and the C: Distribution Library.

## Git
- First commit is the untouched original; never rewrite history on `main`.
- One branch per feature (`feature/...`); merge after the user tests.
