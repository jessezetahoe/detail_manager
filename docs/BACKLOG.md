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
  - [ ] M3 (user, 2026-11-18: next priority after the sidebar; "still almost too much metadata") Search ranking: title first, then scenes, then notes; stop the master file name from matching every detail equally
  - [ ] M4 Manual title overrides for titles the program cannot work out (only if M1 leaves gaps)
- **U Screen layout**
  - [ ] U1 Slim cards: thumbnail, title, one short second line. ANSWERED (Q2, 2026-11-15): second line is the framing type (Solid Joist / Truss Joist / I-Joist, from the master name), with Hydronics added where it occurs, for example "Truss Joist - Hydronics"
  - [x] U2 Sidebar (verified in production 2026-11-18: "side bar looks good for now"; merged): categories with counts (Floor to Beam with its four sub-types indented), source files and the library/thumbnail/staging tools folded away, Diagnostics at the bottom, explanation banner removed. Original request: source file list collapsed by default; filter by CATEGORY instead (user, 2026-11-15: friendly type names such as Foundation, Floor, Roof, Connection, Shear Transfer, worked out from the scrapbook number only, since several scrapbooks share a number). Names kept in an editable `categories.json` next to `abbreviations.json`. Numbers in the index today: 01 FND (8 files), 02 FLR TO FND / RET (24), 03 FLR TO FLR (26), 04 to 07 FLR TO 2PLY / 3PLY / SOLD / STL beam (24 each), 08 ROOF EAVE, 09 ROOF RAKE, 10 ROOF RDGE, 11 ROOF PTCH, 12 ROOF STD, 13 ZE STD (10), 14 CONN (5). ANSWERED 2026-11-15: 04 = Floor to Beam, Flush, Exterior; 05 = Flush, Interior; 06 = Bearing, Exterior; 07 = Bearing, Interior (confirmed against the index: every file of each number carries those two words). Roof (08 to 12): start as ONE category; more roof details are coming, split later by editing `categories.json` (no code change). Build the file so a category can have sub-types.
  - [ ] U5 Source switch above the categories: Library / Old Projects / Both (user, 2026-11-15). Old Projects = job files not yet in the formal library (L3). Show the switch when L3 exists; design U2 so it has room for it
  - [ ] U3 Fuller detail inspector: source, page, all scenes, paths, raw and clean text
  - [ ] U4 More than 80 results (paging or load-more)
- **S SketchUp helper**
  - [ ] S1 Open SketchUp Source to the exact scene; scene buttons for multi-view details
  - [ ] S2 Thumbnail rendering from a menu item instead of the Ruby Console (admin only)
  - [ ] S3 Faster Open Detail on big files: read only the parts of the master the staging file keeps (now the whole file is read, 253 MB for the largest job file; matters over the network). Touches staging: needs a LayOut 2025 check

- **R Releases**
  - [x] R1 Daily-use copy (2026-11-18): `C:\sketchup_dev\detail_manager_release`, made by `tools/publish_local_release.sh` from a committed version (VERSION.txt says which). Own data folder `%LOCALAPPDATA%\ZE Detail Manager` (copied once from the Dev folder), port 8768 like the old program. Development (`RUN_DEV.bat`, Dev folder, port 8769) can no longer affect daily work
  - [ ] R2 The thumbnail worker still writes to the old `ZE Detail Manager Prototype 0.1` folder. Point it at the right data folder before the next render (with S2). Until then, masters changed on Z: show the viewport-only fallback thumbnail (2 found on 2026-11-18)

- **F Field reports (from daily use)**
  - [~] F3 (user, 2026-11-19) LayOut backup files in the library folder ("Backup of (01) FND CONC WSP.layout" and 2 more) were indexed as masters. Now always skipped in both folders: names "Backup of *", "*~.layout", "~$*" (setting `skip_file_patterns`). Already-indexed backups drop out on the next refresh. Built on `feature/old-projects`, user check pending
  - [x] F1 (user, 2026-11-18; verified the same day, merged and published) Searching "hydronics" also found Traditional (no hydronics) details: the TRAD expansion said "Traditional Framing (No Hydronics)". FIXED on branch `fix/abbreviation-noise`: TRAD = "Traditional Framing"; same fix for FILL (was adding "California") and TAIL (was adding "Eave"). Rule for the list: an expansion must not add words the detail does not have (tested). Editing `abbreviations.json` now makes the next Refresh Index re-read every master once (thumbnails kept).
  - [~] F2 (user, 2026-11-18) 3PLY should also be found by "triple", 2PLY by "double". BUILT on branch `fix/field-reports` (collects field fixes until the user has time to check them; not urgent for the daily copy): 2PLY = Double Ply, 3PLY = Triple Ply; abbreviation codes may now start with a digit. Scene names written "3 Ply" (with a space) are covered through the master title, which every detail of that master carries
- **O Non-Library Details (called "Old Projects" until 2026-11-19; decided 2026-11-18)**
  - Approach: read the job LayOut files directly (no PDF re-export). Old Projects = ONE flat drop folder: after a job is finished, its LayOut file is copied in. Every file name starts with the job number, so no duplicates and no subfolders. Leaving a job out = removing its file. Never scan the full projects folder (about 2,000 jobs x 110 to 330 details). Backups never enter the folder. Final program: one Old Projects folder on the server, published with the index like the library
  - Facts from the user: details are grouped (loose viewports are rare: skip them, count them in Diagnostics); every detail has a drawn title of some kind; scene names in jobs are usually SketchUp defaults ("Scene 3"), so never show those as the card's scene line or use them as a title; pasted library details still point to the library models
  - [x] O1 Checked 19 job files (2026-11-18). Results: `docs/reviews/old_projects_check.md`
  - [~] O2 Old Projects as a second source. BUILT 2026-11-18 overnight (branch `feature/old-projects`, which also carries F2), user test pending: Old Projects folder setting (admin tools), Refresh Index reads both folders (each only removes its own masters; an unreachable Old Projects folder leaves everything as it was), Library / Old Projects / Both switch at the top of the sidebar (only shown once Old Projects has files), job list with counts (newest job first), orange JOB badge with job number and sheet on each card, "Both" ranks library details ahead of equally good job details
  - [~] O3 BUILT: card line "Same as Library: <title>" when the job detail uses the same model AND scene as a library detail; otherwise the model kind (Custom model / Old library model / Library model). Library models = models any library master uses. The old-library folder is a setting (`old_library_model_folders`, default `Z:/Google Drive/ZE Sketchup/ZE Detail Scrapbooks`). Not yet: hiding job duplicates when the library version is in the same results
  - [~] O4 BUILT: title box after N.T.S. accepted when the one before is not a title (library unchanged, goldens identical); default scene names never a title nor a card line; fallback = best other text, then page name
  - [ ] O5 Full thumbnails for job details (now the SketchUp-view-only fallback, without labels): comes with the SketchUp render menu (S2/R2)
  - [ ] O6 Show the job detail number (801, 1002 ...) on job cards
  - [x] O7 (user, 2026-11-19) The folder is the one where job-specific details are already kept, each job in its own folder, so they are never archived. The user adds jobs. Job number now also taken from the job folder name when the file name has none
  - [~] O9 (user, 2026-11-19) Renamed in the program to "Non-Library Details" (switch: Library / Non-Library / Both); in Both, job cards carry an orange NON-LIBRARY · JOB badge. Built, user check pending
  - [ ] O8 (user, 2026-11-19) Do not show details that are exactly the same; show a tally instead ("in 40 of 50 jobs") and use it to find the most common details to add to the library. Proposal: "exactly the same" = same SketchUp model and scene for every view AND the same notes; one card per group with "In N jobs" (click: list of jobs, open any copy); a "Most used" sort to list library candidates; job copies of a library detail hidden in Both (the library card says "also used in N jobs"). Sample (3 jobs): 567 details -> 41 groups shared by 2+ jobs on models and scenes, 16 on identical text. Waiting for the user's go

- **C Clipboard (fewer steps than the staging file)**
  - [ ] C1 Find out what LayOut puts on the Windows clipboard when a detail is copied (`tools/clipboard_probe.py`, read only; the user runs it once after copying a detail in LayOut). If the format can be reproduced, Open Detail could become "Copy Detail": the user only presses Ctrl+V in the project. Never AutoHotkey or keystroke automation. If it cannot be reproduced, the staging file stays

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
- [ ] L3 Old Projects search. MOVED UP 2026-11-18 (user's next priority; see O1 to O4 in 0.2)
- [ ] L4 Promote to Library review queue
- [ ] L5 Find details from a SketchUp view (image or model recognition); may move more into SketchUp
- [ ] L6 Favorites, recently used, detail basket (only if users ask)

## Questions for the user
- Q1 Which computers have Python now, and which version? (`py --version`). Only matters until P2
- Q2 ANSWERED 2026-11-15: yes, slimmer card; framing type plus Hydronics where it occurs
- Q3 ANSWERED 2026-11-15: see U2
- Q4 ANSWERED 2026-11-15: the POC 07A index on this computer (182 masters, 5,254 details, built in August) is believed to be the one in daily use
