# To-do list for the next session (in the order to do it)

Updated 2026-11-15. Tags (T3, M1 ...) match `docs/BACKLOG.md`.
Size: S = under an hour, M = a few hours, L = open ended. "Default" is what I would do if you have no preference.

## Where things stand
**Done:** title fix with scene line on cards (verified on the full library 2026-11-15); development copy has its own index (`ZE Detail Manager Dev`); diagnostics log and Diagnostics button (verified 2026-11-15); repo and rules; regression tests (33, passing on your computer) merged to `main`; render files for the 8 test masters in place; user guide draft started (Python requirements).
**Program itself:** Prototype 0.1 plus the diagnostics log. Search, Open Detail and thumbnails are unchanged.
**After a session, push with:** `cd /d C:\sketchup_dev\detail_manager` then `git push origin main`.
**To try the development copy:** double-click `C:\sketchup_dev\detail_manager\RUN_DEV.bat` (own port and its own copy of the index; the daily program is never changed).
**To run the tests:** `cd /d C:\sketchup_dev\detail_manager` then `py -m unittest discover -s tests` (about 40 s, 53 tests, expect `OK`).

## The list, in order
| # | Tag | Item | Size | What I need from you |
|---|---|---|---|---|
| 3 | M2 | **Clean text: BUILT on branch `feature/clean-text`, waiting for your test.** Run the tests (53), `RUN_DEV.bat`, Refresh Index, try searches, open a detail and read its notes | S-M | Your test, then I merge |
| 4 | T3 | Thumbnail crop tests from the render files | S | `py -m pip install pymupdf` once if the tests say it is missing |
| 5 | U1, U3 | Slim cards (title, then framing type and Hydronics) and fuller inspector | M | Look at it in the browser |
| 6 | U2 | Sidebar collapsed, filter by category (from the scrapbook number) | S-M | nothing (answered) |
| 7 | M3, U4 | Search ranking; more than 80 results | M | A few real searches where the order felt wrong |
| 8 | S1 | Open SketchUp to the exact scene | M | Test in SketchUp 2025 |
| 9 | D3 | Local server check | S | nothing |
| 10 | P1, P2 | Standalone program window, packaged (start of 0.3) | L | Test on a second computer |

## How each step goes
1. I make the change on its own branch and run the tests.
2. You run the tests and try it (I give the exact lines to paste).
3. If it is right, I merge to `main` and you push.
Anything that touches Open Detail: you also open the result in LayOut 2025.
