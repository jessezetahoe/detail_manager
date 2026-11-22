# Release history

Version numbers: the last digit for fixes, the middle digit for new features. The version
shows at the top left of the program and in Diagnostics. Each publish to the daily copy
gets a new number and an entry here; the git tag (vX.Y.Z) is set once it is verified.

## 0.3.0 (2026-11-22)
- Filters (chips) under the search box: Joist, Floor system, Beam, Joist at beam, Location,
  Wall (read as phrases: Wall Abv / Wall Abv Blw / Wall Blw / NW ABV / NW), Joist direction, Foundation, Other.
  Click once = must have, twice = must NOT have. Codes can be several words ("NW ABV").
  Live counts per chip; set from master file names and scene names only (never notes);
  editable in chips.json.
- The result count says "80 of 1,234" when there are more matches than shown.

## 0.2.1 (2026-11-22)
- Fix: a LayOut file containing characters XML does not allow (e.g. an invisible control
  character inside a SketchUp tag name, found in job 1827 S0.3) is now read instead of being
  rejected. Staging files keep those characters byte-for-byte. Diagnostics/log notes such files.
- Version number shown at the top left and in Diagnostics.

## 0.2.0 (2026-11-22) - everything since Prototype 0.1
- Regression test suite on real masters; diagnostics log and Diagnostics panel
- Real titles (text beside N.T.S.) with the scene as a second line; clean notes (raw text kept)
- Category sidebar (from the scrapbook number); abbreviation fixes (hydronics, 2PLY/3PLY)
- Non-Library Details (job files): Library / Non-Library / Both, job list, exact-duplicate
  tally ("In N jobs"), most-used sort, library copies hidden in Both; backups and off-sheet
  details left out
- Detail cart (several details to LayOut at once, one staging file each)
- How To page (How To button)
- Render only new or changed masters; render from the toolkit menu with a progress window;
  Open in SketchUp at the detail's scene (needs the Zachary Engineering Toolkit)

## Prototype 0.1 (handoff from ChatGPT)
- Stable POC07A code path: index, search, full thumbnails, Open Detail staging
