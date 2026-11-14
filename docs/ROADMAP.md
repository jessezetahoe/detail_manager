# Roadmap

## Delivery shape (decided 2026-11-14)
- **Standalone Windows program** is the target; the browser/localhost GUI was a test harness.
- Proposed: keep the validated Python core (parser, index, staging) and the HTML UI,
  hosted in a native window (pywebview / Edge WebView2), packaged with PyInstaller so
  users need no Python install. Removes the localhost port entirely.
- **Small SketchUp extension** alongside it for what must run inside SketchUp:
  thumbnail render queue, open model to exact scene, and later "find details like
  this view" (context/visual search) sending the current view to the app.
- Not running the whole app inside SketchUp: indexing 10k+ details would block
  SketchUp's single UI thread, and the core would need a Ruby rewrite.

## 0.2 - safety net + UI/data cleanup
1. Regression tests on real fixtures (detection, multi-viewport, staging, search, read-only masters).
2. Persistent diagnostics log in %LOCALAPPDATA%.
3. Collapsed sidebar, slim cards (thumbnail + title + one descriptor), fuller inspector.
4. Raw / clean / display metadata; filter bubble numbers; fix title inference.
5. Open SketchUp to exact scene.

## 0.3 - standalone + deployment/admin
Native window + packaged runtime, published central index with local copies,
update detection, admin/status screen, user and admin guides.

## Later
SKP dependency tracking, controlled reference maintenance, Job Archive search,
Promote to Library, visual/context search.
