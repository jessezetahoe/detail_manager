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
  - [x] D1 (verified by the user 2026-11-15, merged) Persistent log in the data folder (`logs\detail_manager.log`, 1 MB x 4 files): start-up, index runs and errors, thumbnail warnings, Open Detail, failed commands. Never in the library or job folders. BUILT 2026-11-15 (branch `feature/diagnostics-log`), user test pending
  - [x] D2 (verified by the user 2026-11-15: opens, counts match) Diagnostics button (bottom of the left panel, red count when something is wrong): library reachable or not, counts, masters that failed to index, last SketchUp render result, recent log entries, Open Log Folder. BUILT, user test pending
  - [x] D4a An unreachable library folder can no longer be read as "every master was deleted" (refresh stops with a logged error; before, starting with `--library` while Z: was offline would have emptied the index and its thumbnails)
  - [ ] D4b Same protection when the drive drops out part-way through a scan (some masters seem to vanish): do not purge when a large share is missing; ask first
  - [x] D5 `RUN_DEV.bat`: runs the development copy on its own port (8769) beside the daily program, reading the same index (`ZE Detail Manager POC 07A`). DONE 2026-11-15: `RUN_DEV.bat` now makes a one-time copy (about 7 GB, `%LOCALAPPDATA%\ZE Detail Manager Dev`) and the development copy only ever uses that; the daily program and its index are never touched
  - [ ] D3 Only accept commands from the program's own window (closes the local web server gap). Goes away by itself with P1
- **M Metadata and titles**
  - [x] M1 Title fix (verified by the user 2026-11-15 on the full library: 182 masters re-read, thumbnails kept, the 110 titles look reasonable; merged). The title is the text box just before the "N.T.S." box; fallback is the scene name, then the page name. Checked: all 149 test details and all 5,254 details in the August index have exactly one N.T.S. with a real title before it. FINDING: there are only 110 different titles for 5,254 details ("Interior Footing - Perp to Para" and the like are shared by dozens), so the scene name is what tells details apart: cards now show the scene in plain words under the title, with "(+1 more view)" for multi-view details. Drawn titles are NOT run through the abbreviation list (it would turn "Wood Post" into "Wood Post or Column"). Review list: `docs/reviews/titles_full_library.md`
  - [x] M1a Re-reading rules have a version number (`INDEX_VERSION`, stored per master). After a rule change, Refresh Index re-reads every master once and KEEPS the full thumbnails and render files (the master itself did not change)
  - [x] M2 Raw / clean / notes text (verified 2026-11-18: callouts clean "for the most part"; user: still almost too much metadata, searches need tightening -> M3). Dropped from search and display: text boxes that are only a 1 to 3 digit number (bubbles, table cells; 60% of all text lines in the library), "N.T.S.", and a lone "XXX". Kept: everything else, including dimensions (`2 1/4"`, `1/4`), `(2) A35`, and "XXX" inside a note ("PER DTL XXX"). Raw text is stored untouched in its own column (proved identical to what Prototype 0.1 read, 149 of 149). The detail window shows the notes (clean text without the title) with the raw text behind a fold-out. Index version 3: one Refresh Index re-reads the masters, thumbnails kept
  - [ ] M3 Search ranking: title first, then scenes, then notes; stop the master file name from matching every detail equally
  - [ ] M4 Manual title overrides for titles the program cannot work out (only if M1 leaves gaps)
- **U Screen layout**
  - [ ] U1 Slim cards: thumbnail, title, one short second line. ANSWERED (Q2, 2026-11-15): second line is the framing type (Solid Joist / Truss Joist / I-Joist, from the master name), with Hydronics added where it occurs, for example "Truss Joist - Hydronics"
  - [ ] U2 Sidebar: source file list collapsed by default; filter by CATEGORY instead (user, 2026-11-15: friendly type names such as Foundation, Floor, Roof, Connection, Shear Transfer, worked out from the scrapbook number only, since several scrapbooks share a number). Names kept in an editable `categories.json` next to `abbreviations.json`. Numbers in the index today: 01 FND (8 files), 02 FLR TO FND / RET (24), 03 FLR TO FLR (26), 04 to 07 FLR TO 2PLY / 3PLY / SOLD / STL beam (24 each), 08 ROOF EAVE, 09 ROOF RAKE, 10 ROOF RDGE, 11 ROOF PTCH, 12 ROOF STD, 13 ZE STD (10), 14 CONN (5). ANSWERED 2026-11-15: 04 = Floor to Beam, Flush, Exterior; 05 = Flush, Interior; 06 = Bearing, Exterior; 07 = Bearing, Interior (confirmed against the index: every file of each number carries those two words). Roof (08 to 12): start as ONE category; more roof details are coming, split later by editing `categories.json` (no code change). Build the file so a category can have sub-types.
  - [ ] U5 Source switch above the categories: Library / Old Projects / Both (user, 2026-11-15). Old Projects = job files not yet in the formal library (L3). Show the switch when L3 exists; design U2 so it has room for it
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
- [ ] L3 Job Archive search = "Old Projects" (second source, clearly labelled; see U5)
- [ ] L4 Promote to Library review queue
- [ ] L5 Find details from a SketchUp view (image or model recognition); may move more into SketchUp
- [ ] L6 Favorites, recently used, detail basket (only if users ask)

## Questions for the user
- Q1 Which computers have Python now, and which version? (`py --version`). Only matters until P2
- Q2 ANSWERED 2026-11-15: yes, slimmer card; framing type plus Hydronics where it occurs
- Q3 ANSWERED 2026-11-15: see U2
- Q4 ANSWERED 2026-11-15: the POC 07A index on this computer (182 masters, 5,254 details, built in August) is believed to be the one in daily use
