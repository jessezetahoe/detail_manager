# To-do list for the next session (in the order to do it)

Updated 2026-11-18. Tags (M3, U1 ...) match `docs/BACKLOG.md`.
Size: S = under an hour, M = a few hours, L = open ended.

## Where things stand
**In daily use:** `C:\sketchup_dev\detail_manager_release` (desktop shortcut), built from `main` at the sidebar release.
Its data: `%LOCALAPPDATA%\ZE Detail Manager`. It only changes when Claude publishes a tested version.
**Done and verified:** regression tests, diagnostics log and button, real titles with the scene line,
clean notes (raw text kept), category sidebar.
**Development copy:** `RUN_DEV.bat` (port 8769, data in `%LOCALAPPDATA%\ZE Detail Manager Dev`).
**Tests:** `cd /d C:\sketchup_dev\detail_manager` then `py -m unittest discover -s tests` (63 tests, about 40 s, expect `OK`).
**Push after a session:** `cd /d C:\sketchup_dev\detail_manager` then `git push origin main`.

## The list, in order
| # | Tag | Item | Size | What I need from you |
|---|---|---|---|---|
| 0 | F1 | **Hydronics search fix: BUILT on branch `fix/abbreviation-noise`.** Check "hydronics" in the development copy after Refresh Index, then I publish it | S | Your check |
| 1 | M3 | **Tighter search.** Rank title first, then scene, then notes; stop the master file name from matching every detail the same; fewer loose matches from notes | M | 3 to 5 real searches where the results felt too broad or in the wrong order |
| 2 | U1, U3 | **Slim cards and fuller detail window.** Card: thumbnail, title, scene line, framing type with Hydronics. Everything else (source, page, all scenes, paths, notes, raw text) in the detail window | M | Look at it and say what to trim |
| 3 | U4 | More than 80 results (load more as you scroll) | S | nothing |
| 4 | R2, S2 | **Thumbnail render from a SketchUp menu** instead of the Ruby Console, writing to the right data folder. Re-renders the 2 masters changed since August | M | Run it once in SketchUp 2025 |
| 5 | S1 | **Open SketchUp Source to the exact scene**; one button per scene for multi-view details | M | Test in SketchUp 2025 |
| 6 | T3 | Thumbnail crop tests from the render files | S | `py -m pip install pymupdf` once if asked |
| 7 | D3, D4b | Small safety items: only the program's own page may send it commands; do not drop masters from the index if the drive drops out mid-scan | S | nothing |
| 8 | P1, P2 | **Standalone program** (start of 0.3): its own window instead of a browser tab, packaged so no Python install is needed | L | Test on a second computer |
| 9 | P3 to P5, G1, G2 | Company rollout: one published index on the server, local copies, update check, admin screen, User Guide and Admin Guide | L | Server location; who maintains the index |

## Later (after rollout)
Which masters use a given SketchUp model (L1), controlled reference updates (L2), Old Projects search (L3, L4), find details from a SketchUp view (L5), favorites (L6).

## How each step goes
1. I build it on its own branch and run the tests.
2. You run the tests and try it in the development copy (exact lines given).
3. If it is right, I merge to `main`, publish it to the daily copy, and you push.
Anything that touches Open Detail: you also open the result in LayOut 2025.
