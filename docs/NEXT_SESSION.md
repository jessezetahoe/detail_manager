# To-do list for the next session (in the order to do it)

Updated 2026-11-22. Tags (M3, A3 ...) match `docs/BACKLOG.md`.
Size: S = under an hour, M = a few hours, L = open ended.

## Where things stand
- **Daily copy: version 0.3.1** (0.4.0 with typo tolerance + scroll loading on `feature/typos-scroll`, testing) (2026-11-22, tag v0.3.1; see `docs/RELEASE_HISTORY.md`).
  `C:\sketchup_dev\detail_manager_release`, data in `%LOCALAPPDATA%\ZE Detail Manager`, port 8768.
  It only changes when Claude publishes a tested version.
- **Has:** real titles + scene line, clean notes, categories, Non-Library Details (job files) with
  duplicate tally, cart, How To page, render only changed masters, SketchUp helper in the toolkit
  (Open at scene, Render Thumbnails menu with progress), tolerant reading of odd characters,
  Filters (chips) with "one choice" groups.
- **Development copy:** `RUN_DEV.bat` (port 8769, data in `%LOCALAPPDATA%\ZE Detail Manager Dev`).
- **Tests:** `cd /d C:\sketchup_dev\detail_manager` then `py -m unittest discover -s tests`
  (126 tests, about 75 s, expect `OK`).
- **Push after a session:** `cd /d C:\sketchup_dev\detail_manager`, `git push`, `git push --tags`.
  Toolkit: `cd /d C:\sketchup_dev\zachary_plugin`, `git push`.

## The list, in order
| # | Tag | Item | Size | What I need from you |
|---|---|---|---|---|
| 1 | M3 | **Tighter search ranking**: title first, then scene, then notes; master file name no longer matches every detail equally | M | 3 to 5 real searches that felt off (from daily use) |
| 2 | A3 | **Plain-English search**: "hanger at steel beam, wall below, I-joist" sets the chips + search words; shows what it understood as chips you can click off. Offline, rule based, editable file | M | A handful of sentences the way you would type them |
| 4 | U1, U3 | Slim cards (thumbnail, title, scene line, framing type + Hydronics); fuller detail window | M | Say what to trim |
| 6 | O6, O10 | Job cards: show the job detail number (801, 1002 ...); review job details that got a note as title | S | Once more jobs are loaded |
| 7 | S3 | Faster Open Detail on big job files (read only what the staging file keeps) | M | Open the result in LayOut 2025 |
| 8 | D3, D4b, T3 | Small safety items: only the program's own page may send commands; don't drop masters if the drive drops out mid-scan; thumbnail crop tests | S | nothing |
| 9 | X1 | Retired details (RETIRED overlay, "replaced by"); kept in Detail Manager data, never in the masters, survives master updates | M | Decide how it should look / who marks them |
| 10 | X2 | Job tags (state, architect, builder, city, year) from one `jobs.csv` in the Non-Library folder | M | When more jobs are loaded |
| 11 | A6 | Scene renaming in library models: test on a throwaway model + LayOut file first (viewports must stay linked) | M | Only when you want it |
| 12 | P1, P2 | **Standalone program** (own window, no Python install needed) | L | Test on a second computer |
| 13 | P3-P5, G1, G2 | Company rollout: one published index on the server, local copies, update check, admin screen, User Guide, Admin Guide | L | Server location; who maintains the index |
| 14 | A5 | Meaning-based search with a small model bundled in the program (offline, nothing sent out, no tokens, no cost) | L | Later |

## Later (after rollout)
Several details in one staging file (C4), which masters use a given model (L1), controlled reference
updates (L2), Promote to Library queue (L4), find details from a SketchUp view (L5), favorites (L6).

## How each step goes
1. I build it on its own branch, run the tests, and update the How To page in the same change.
2. You try it in the development copy (`RUN_DEV.bat`).
3. If it is right, I bump the version, merge to `main`, publish to the daily copy, tag it, and you push.
Anything that touches Open Detail: you also open the result in LayOut 2025.
