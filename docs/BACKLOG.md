# Backlog (tags to refer to while we work)

Status key: [ ] not started, [~] in progress, [x] done and verified.
Rules that never change are in `CLAUDE.md`. Background is in `docs/handoff/`.

## Done
- [x] Repo set up; first commit is the untouched ChatGPT handoff (Prototype 0.1)
- [x] T1 Regression tests: 33 tests on 8 company masters (149 details). Pass in the
      dev environment and on the user's Windows computer (2026-11-15). Merged to `main`
- [x] T2 Thumbnail render files for the 8 test masters copied into `tests/fixtures/renders/`
      (from `%LOCALAPPDATA%\ZE Detail Manager POC 07A\thumbnail_renders`; local only, not in git)

## 0.2 - safety net and cleanup
- **T Tests**
  - [ ] T3 Thumbnail crop tests using the render files (needs PyMuPDF where the tests run)
- **D Diagnostics**
  - [ ] D1 Persistent log in %LOCALAPPDATA% (index errors, thumbnail warnings). Never in the library or job folders
  - [ ] D2 Show the last errors in the program instead of a toast that disappears
  - [ ] D3 Only accept commands from the program's own window (closes the local web server gap). Goes away by itself with P1
- **M Metadata and titles**
  - [ ] M1 Title fix: find the real title next to "N.T.S." (they are in separate text boxes); fall back to the scene name
  - [ ] M2 Raw / clean / display text. Clean and display drop bubble numbers, table-cell numbers and "N.T.S."; raw text is kept
  - [ ] M3 Search ranking: title first, then scenes, then notes; stop the master file name from matching every detail equally
  - [ ] M4 Manual title overrides for titles the program cannot work out (only if M1 leaves gaps)
- **U Screen layout**
  - [ ] U1 Slim cards: thumbnail, title, one short descriptor (Q2)
  - [ ] U2 Sidebar: source file list collapsed by default; filters instead (Q3)
  - [ ] U3 Fuller detail inspector: source, page, all scenes, paths, raw and clean text
  - [ ] U4 More than 80 results (paging or load-more)
- **S SketchUp helper**
  - [ ] S1 Open SketchUp Source to the exact scene; scene buttons for multi-view details
  - [ ] S2 Thumbnail rendering from a menu item instead of the Ruby Console (admin only)

## 0.3 - standalone program and rollout
- [ ] P1 Program window instead of a browser tab (same screens, no local web server)
- [ ] P2 Packaged program: staff need no Python (see `USER_GUIDE_DRAFT.md`)
- [ ] P3 One published index and thumbnail set on the server; each computer keeps a local copy
- [ ] P4 "Library update available" check and local update
- [ ] P5 Admin/status screen (library path, versions, counts, failed masters, last render)
- [ ] P6 Only changed masters are re-indexed and re-rendered (formalize what exists)
- [ ] G1 User Guide (draft started: Python requirements)
- [ ] G2 Installation / Admin Guide

## Later
- [ ] L1 Which masters and details use a given SketchUp model (dependency tracking)
- [ ] L2 Controlled, explicit master reference maintenance (never automatic)
- [ ] L3 Job Archive search (second library, clearly labelled)
- [ ] L4 Promote to Library review queue
- [ ] L5 Find details from a SketchUp view (image or model recognition); may move more into SketchUp
- [ ] L6 Favorites, recently used, detail basket (only if users ask)

## Questions for the user
- Q1 Which computers have Python now, and which version? (`py --version`). Only matters until P2
- Q2 U1: is the framing type (Solid Joist / Truss Joist / I-Joist, from the master name) the right second line on a card?
- Q3 U2: what would you filter by? Default: the scrapbook number groups ((01) FND, (02) FLR TO FND, ...)
- Q4 Is this computer's library index (POC 07A, built in August) the one you use day to day, or is there a newer Prototype 0.1 index elsewhere?
