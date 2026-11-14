# Detail Manager — Claude Code Handoff

**Handoff date:** 2026-11-14  
**Current stable baseline:** **Detail Manager Prototype 0.1**, derived from the stable **POC 07A** code path.  
**Status:** Working prototype, used in real production, full company library successfully indexed/rendered without crashes, and a smaller C:-based Distribution Library was successfully installed and tested on a separate presentation computer.

---

## 1. Read this first

This project is no longer a proof-of-concept about whether LayOut files can be indexed. That question has been answered.

The current system:

- indexes a very large SketchUp LayOut detail library;
- identifies one searchable detail as one top-level LayOut group containing one or more SketchUp viewports;
- extracts searchable text, source data, SketchUp reference paths, scene names/PIDs, and cached viewport previews;
- builds a local SQLite/FTS index;
- searches the library quickly through a local browser GUI;
- creates finished full-detail previews that include LayOut labels/callouts;
- creates disposable one-detail `.layout` staging files without changing the master;
- opens the master LayOut and SketchUp source files;
- preserves exact master reference paths;
- supports multi-viewport details as a single detail/result;
- has been used in production and saves time.

The next development phase should be **productization and workflow improvement**, not a rewrite.

### Non-negotiable rule

**Start from the files in `CURRENT_STABLE_SOURCE/`. Do not start from POC 07B/07C/07D/07E.**

The later crop experiments were less stable and were deliberately abandoned.

---

# 2. User / environment

The primary user is a structural engineer working heavily in:

- SketchUp
- LayOut
- Windows 11
- mapped/network drives
- large structural detail libraries

Current preferred production versions:

- **LayOut 2025** is the conservative/current working choice.
- SketchUp 2025 is a safe target for the current workflow.
- Later SketchUp/LayOut versions were considered too buggy for the user's production workflow at the time of development.

The user is comfortable with scripts and prototype utilities, but the final system should be usable by ordinary company employees without understanding Python, XML, Ruby consoles, or LayOut internals.

---

# 3. Core business problem

The company has a very large structural detail library:

- roughly **10,000+ details**
- roughly **180 master `.layout` scrapbook files**
- each master LayOut file can contain multiple pages;
- each sheet/page can contain multiple grouped details;
- each detail normally contains:
  - one or more SketchUp model viewports;
  - LayOut text/callouts/leaders/notes;
  - all grouped together as one top-level LayOut group.

Historically, the library workflow was cumbersome:

1. Navigate a hyperlinked PDF/tree.
2. Find a detail page.
3. Click/open the master `.layout`.
4. Scroll to the page/detail.
5. Copy the grouped detail.
6. Paste it into a project.
7. Close the master.

The goal of Detail Manager is to make this:

> Search → visually identify → Open Detail → copy/paste.

---

# 4. Detail model / grouping rules

## Searchable detail definition

The tested rule is:

> **One searchable detail = one top-level LayOut group containing one or more SketchUp viewports (`skpModelRef`).**

This rule has worked well across the tested library.

Important:

- Some top-level groups are not details, e.g. `NEW` markers or `FUTURE RELEASE` notes.
- Those groups contain no SketchUp viewport and should be ignored.
- A detail may contain **1 to 5+ SketchUp viewports**.
- All viewports inside one detail group must remain:
  - one search result;
  - one finished preview;
  - one staging/copy unit.

Representative multi-view case tested:

- King Stud detail with:
  - `King Stud Blw`
  - `King Stud Abv`

These two SketchUp viewports are one detail.

---

# 5. Critical path/reference constraints

This is one of the most important parts of the project.

## NEVER rewrite master paths

The master LayOut files contain exact SketchUp reference paths such as:

`Z:/Google Drive/ZE Library/ZE Scrapbooks/_Models/(03) FLR TO FLR/(03) FLR TO FLR SJ.skp`

These paths must **not** be:

- normalized;
- changed to UNC;
- made relative;
- relinked;
- rewritten to another slash style;
- silently repaired;
- replaced with copied local SKPs.

The current indexer intentionally preserves the path spelling used in the file/discovery process.

### Why this matters

Even an apparently harmless change to a LayOut reference can create downstream problems.

The company also has mirrored server drives at different physical locations. That is acceptable as long as each workstation sees the library under the same logical mapped path.

---

# 6. Do not unlink SketchUp references

A major discovery during testing:

Native LayOut copy/paste automatically consolidates multiple inserted details that point to the same underlying SketchUp source.

Tests:

- `TEST 0.layout`: blank, no SKP ref.
- `TEST 1.layout`: first pasted detail → one SKP reference.
- `TEST 2.layout`: second different detail from same SKP → still one SKP reference.
- `TEST 3.layout`: additional detail copied from a different master LayOut but same SKP → still one SKP reference.
- `TEST 4.layout` / `TEST 5.layout`: additional details continued to share the same reference.

The embedded SKP hash remained unchanged.

**Conclusion:**

Do not “unlink” or explode SketchUp references when inserting details.

The current `Open Detail` staging workflow intentionally leaves LayOut/SketchUp reference behavior native so that normal LayOut copy/paste can do this consolidation.

---

# 7. Project-detail behavior after insertion

Once a detail has been copied into a project:

- Detail Manager does **not** manage that project detail.
- Future changes to the master library should not be automatically propagated into project files.
- Detail Manager is a library/search/insertion aid, not a project reference synchronization system.

However:

- the pasted details should retain normal LayOut reference consolidation;
- multiple related details can share a single project-local underlying SketchUp reference as LayOut normally does.

---

# 8. LayOut package findings

`.layout` files are ZIP-like packages containing XML plus referenced/cached payloads.

Important members include:

- `document.xml`
- `references.xml`
- page XML files
- embedded/reference `.skp`
- cached viewport images
- vector caches
- styles and other data

The indexer reads these packages directly.

## Version compatibility test

A representative library file was tested as:

- original LayOut 2021:
  - `21.1.332`
- saved as LayOut 2025:
  - `25.0.660`

The save rewrote XML/caches, but the semantic structure remained stable:

- same page IDs;
- same viewport IDs;
- same `skpModelRef` IDs;
- same scene names/PIDs;
- same SKP reference identity;
- same exact external SketchUp path.

**Design implication:** Parse semantic structure, not exact XML formatting.

---

# 9. Current stable application files

The canonical source for continuation is in:

`CURRENT_STABLE_SOURCE/`

Main files:

## `detail_manager.py`

Single-file Python application containing:

- LayOut ZIP/XML parser;
- text/RTF extraction;
- abbreviation expansion;
- SQLite database;
- FTS5 search;
- incremental indexing;
- staging `.layout` builder;
- thumbnail queue processing;
- local HTTP API;
- embedded HTML/CSS/JS GUI.

Current stable SHA-256:

`d52bee81b881ac9816d64e2dbd522bf631c740a12d59722205548554f90896e9`

## `thumbnail_worker.rb`

Ruby script run from the SketchUp Ruby Console.

Purpose:

- reads the Detail Manager render queue;
- opens master LayOut files using the LayOut Ruby API;
- temporarily hides configured layers (default `GUIDES`);
- exports full pages as PDF;
- restores layer visibility in memory;
- **never saves the master LayOut file**;
- writes a render manifest.

Current stable SHA-256:

`265d9fb5228ad0a077c1d5ba1f561cdb67a7242899e0dccc24e3e1a26545f24e`

## `abbreviations.json`

Externally editable abbreviation mapping.

Current stable SHA-256:

`1c74957c26f59c0bd8bcf9424d50132900e2f847004d54d9af14c17dd623d976`

Other source/setup files are included in the handoff package.

---

# 10. Current application data location

Prototype 0.1 uses:

`%LOCALAPPDATA%\ZE Detail Manager Prototype 0.1\`

Current tree:

```text
ZE Detail Manager Prototype 0.1\
    detail_library.sqlite
    config.json
    previews\
    full_previews\
    staging\
    thumbnail_renders\
    thumbnail_jobs\
```

The older development build used:

`%LOCALAPPDATA%\ZE Detail Manager POC 07A\`

Core logic is the same; the Prototype 0.1 package changed branding/app-data location for a clean presentation installation.

---

# 11. Database schema

SQLite database:

`detail_library.sqlite`

Uses WAL mode.

## `layout_files`

```text
layout_file TEXT PRIMARY KEY
layout_filename TEXT
size_bytes INTEGER
mtime_ns INTEGER
page_count INTEGER
detail_count INTEGER
skp_reference_count INTEGER
last_indexed_utc TEXT
last_error TEXT
```

Used for:

- incremental change detection;
- source file sidebar;
- error tracking.

A file is currently considered unchanged when:

- size matches;
- `mtime_ns` matches;
- prior record has no error.

## `skp_references`

```text
layout_file TEXT
skp_ref_id TEXT
external_path_exact TEXT
internal_target TEXT
PRIMARY KEY(layout_file, skp_ref_id)
```

This is important groundwork for future dependency tracking.

## `details`

```text
detail_key TEXT PRIMARY KEY
layout_file TEXT
layout_filename TEXT
page_ref_id TEXT
page_xml TEXT
page_name TEXT
page_index INTEGER
group_index INTEGER
viewport_count INTEGER
primary_viewport_id TEXT
primary_scene_name TEXT
primary_scene_pid TEXT
display_title TEXT
expanded_title TEXT
master_title TEXT
skp_paths_exact TEXT          -- JSON
bounds_json TEXT              -- JSON
full_preview_relpath TEXT
searchable_text TEXT
```

## `viewports`

```text
detail_key TEXT
viewport_id TEXT
scene_name TEXT
scene_pid TEXT
skp_ref_id TEXT
image_ref_id TEXT
vector_ref_id TEXT
preview_relpath TEXT
PRIMARY KEY(detail_key, viewport_id)
```

## FTS table

If FTS5 is available:

```text
detail_search(detail_key UNINDEXED, searchable_text)
```

Search falls back to `LIKE` if FTS fails.

---

# 12. Current detail key

Current detail key is:

```text
<exact layout path>|<page_ref_id>|<primary_viewport_id>
```

This has worked, but if the code is eventually refactored, be careful about changing persistent IDs because local caches and database relationships depend on the key.

---

# 13. Indexer behavior

Relevant function:

`index_library(library_root)`

Behavior:

1. Recursively scans `*.layout`.
2. Compares discovered files against current DB.
3. Removes DB/cache entries for masters that no longer exist.
4. For existing files:
   - compares file size + nanosecond modification time;
   - skips unchanged files.
5. Changed files are reparsed.
6. Preview data is built in a temporary cache folder.
7. Database replacement happens transactionally.
8. Old full-preview/render caches for a changed master are deleted.
9. Errors are stored without crashing the entire library run.

This has successfully processed the **entire company LayOut library** without a crash.

The user spot-tested results and used the system in real work.

---

# 14. Parsing logic

Relevant function:

`parse_layout(layout_path, preview_dir)`

Main logic:

1. Open `.layout` as ZIP.
2. Require:
   - `document.xml`
   - `references.xml`
3. Parse page references.
4. Parse:
   - page file references;
   - SKP file references;
   - image file references;
   - vector file references.
5. Open each page XML in document page order.
6. Read the top-level page entity list.
7. For each top-level `group`:
   - find all descendant `skpModelRef` entities;
   - ignore group if none exist;
   - treat it as one detail otherwise.
8. For each viewport:
   - scene name;
   - scene persistent ID;
   - SKP reference ID;
   - image/vector reference IDs;
   - cached image preview.
9. Extract all LayOut RTF text in the group.
10. Compute approximate group bounds.
11. Build title/search data.
12. Store one detail record + N viewport records.

### Important tested assumption

No representative masters showed loose SketchUp viewports outside the top-level detail groups.

If Claude discovers exceptions in future libraries, do not silently change the core rule without testing the effect on existing masters.

---

# 15. RTF/text extraction

LayOut text is extracted from `rtfTextRep`.

Current parser converts common RTF constructs and strips formatting.

This gives useful searchable text, but it currently also captures unhelpful text such as isolated numbered detail bubbles.

Example issue:

```text
1
2
3
4
```

from callout/detail bubbles can appear in metadata/search text.

## Planned fix

Do **not** delete raw text.

Instead create three conceptual layers:

1. **Raw metadata**
   - exact extracted text;
   - retained for diagnostics and future parsing.

2. **Clean/search metadata**
   - filter isolated numeric bubble callouts;
   - preserve meaningful strings such as:
     - `2X6 STUD`
     - `(2) A35`
     - dimensions/real notes where appropriate.

3. **Display metadata**
   - the small subset worth showing to the user.

This is a high-priority UI/data cleanup feature.

---

# 16. Titles and abbreviations

Current external mapping:

`abbreviations.json`

Important behavior:

- expand exact tokens only;
- unknown shorthand remains untouched;
- raw source text remains searchable;
- expanded title is also searchable.

Explicit user requirement:

`TJI` → `I-Joist`

but raw `TJI` must still remain searchable.

The current mapping contains many structural abbreviations. Do not hard-code all title behavior into source; keep the external editable JSON.

## Current title concepts

- `display_title`
- `expanded_title`
- `master_title`

`master_title` is derived from the master LayOut filename after removing a leading numeric scrapbook prefix such as `(03)` and expanding known abbreviations.

Future possibility:

- manual title overrides for poor automatically generated titles.

---

# 17. Search

Current search:

- SQLite FTS5 if available;
- BM25 ordering;
- prefix matching on tokenized terms;
- default result limit: **80**;
- optional source `.layout` filter.

Searchable text includes combinations of:

- master filename;
- intended master title;
- page name;
- expanded page name;
- inferred detail title;
- expanded title;
- SketchUp scene names;
- expanded scene names;
- extracted LayOut text.

Search quality is useful in production, but ranking can be improved later based on real queries.

Future ranking should likely weight:

1. intended title;
2. scene/title;
3. expanded abbreviations;
4. metadata text;

rather than treating every text source equally.

---

# 18. Preview architecture

There are two preview systems.

## A. Cached viewport previews

Extracted directly from the `.layout` ZIP image references.

Pros:

- very fast;
- no LayOut render needed.

Cons:

- only show SketchUp viewport imagery;
- do **not** include LayOut labels/callouts;
- multi-view details show several individual viewport tiles.

They remain useful as fallback previews.

## B. Full-detail previews

Preferred visual result.

Workflow:

1. Python creates render queue.
2. Ruby worker opens each master through LayOut API.
3. Worker hides `GUIDES`.
4. Worker exports the full master/pages to PDF.
5. Python/PyMuPDF rasterizes/crops each detail using indexed group bounds.
6. Result stored in local `full_previews`.

This shows:

- SketchUp viewport(s);
- LayOut labels;
- leaders;
- notes/callouts;

as one coherent detail card.

---

# 19. Stable thumbnail crop — DO NOT “FIX” immediately

Current stable crop:

```text
DPI:     220
Left:    0.025 in
Right:   0.025 in
Top:     0.010 in
Bottom:  0.025 in
```

Function:

`process_thumbnail_renders(...)`

These margins are intentionally modest.

The full-library user test concluded this version is stable and useful, even though it may sometimes include a small amount of neighboring sheet content.

### User decision

Stop spending development time chasing perfect crop isolation unless it becomes a genuine usability problem.

---

# 20. Thumbnail experiments that FAILED / should not be revived casually

## POC 06 — direct PNG export

LayOut API `doc.export` returned success, but expected PNG output was not consistently discoverable/usable.

Decision:

- abandoned direct PNG workflow;
- PDF export is deterministic and works.

## POC 06C — PDF export

This worked.

Current stable full-thumbnail pipeline is based on this approach.

## POC 07B — tighter static margins

Margins were tightened further.

Result:

- still caught neighboring details;
- not enough benefit;
- user preferred first crop adjustment.

Abandoned.

## POC 07C — LayOut API visible-entity bounds

Attempted to calculate crop bounds through LayOut API entities.

Diagnostics showed:

- all 129 test details matched;
- `GUIDES` was found;
- but all matches used nearest-center;
- child entity coordinates were in local group coordinate systems;
- transformed coordinates were wrong.

## POC 07D

Attempted group-index + nested transforms.

Failed because code assumed `Page#entities` would contain `Layout::Group` objects.

It does not.

## POC 07E

Recovered root groups from leaf entities and attempted transformation fixes.

Result:

- thumbnails grabbed additional unrelated text/content;
- user explicitly requested reverting to stable first crop-adjusted version.

### Final decision

**07A crop behavior is the stable baseline.**

Do not build future work on 07C/07D/07E unless there is a deliberate research task to revisit page-space transformation behavior.

---

# 21. Hiding GUIDES

Full-detail previews are much cleaner if the LayOut layer:

`GUIDES`

is hidden during render.

Current worker:

- matches configured layer names case-insensitively by exact name;
- default is `GUIDES`;
- snapshots page visibility;
- temporarily turns the layer off;
- exports;
- restores original visibility in memory;
- does not save the master.

The hidden-layer list is configurable and stored in app config.

---

# 22. Staging / Open Detail

This is a major successful part of the project.

User action:

**Open Detail**

Current function:

`build_staging(detail_key)`

It directly manipulates a disposable copy of the `.layout` ZIP/XML package.

## Goal

Create a lightweight one-detail `.layout` file that:

- has one page;
- contains the entire target top-level detail group;
- retains all SketchUp viewports in that group;
- retains associated LayOut labels/callouts/connections;
- retains required references;
- retains exact external SKP paths;
- retains embedded SKP data;
- preserves source LayOut version metadata;
- removes unrelated pages/details/caches.

The master source is read-only.

## Why direct package staging is used

Initial API worker staging cloned a source document through LayOut API.

Problem:

- when run through a newer SketchUp/LayOut API, opening the staging file in LayOut 2025 produced a “created in newer version” warning.

Direct ZIP/XML package manipulation preserves the original source version metadata and avoids that warning.

### Validation

POC 03C:

- source LayOut 25.0.660;
- staging LayOut 25.0.660;
- one page;
- one target detail;
- exact external SKP path preserved;
- embedded SKP SHA-256 preserved;
- viewport caches retained;
- source ~33.19 MiB;
- staging ~11.63 MiB;
- ~65% reduction.

See:

`REFERENCE_REPORTS/POC03C_VALIDATION_REPORT.txt`

---

# 23. Current insertion workflow

Current normal workflow after clicking **Open Detail**:

1. Detail Manager creates local disposable staging `.layout`.
2. Opens it in LayOut.
3. User:
   - `Ctrl+A`
   - `Ctrl+C`
4. Close staging.
5. Return to project.
6. `Ctrl+V`

This is intentionally simple because native copy/paste is proven to preserve/consolidate SketchUp references correctly.

---

# 24. AutoHotkey — DO NOT USE

A prototype considered AutoHotkey to automate:

- open staging;
- select/copy;
- close;
- paste into project.

The user has had poor prior experiences with AutoHotkey and explicitly rejected this direction.

**Do not revive AutoHotkey.**

Long-term one-click insertion could be reconsidered only with a robust compiled Windows/UI automation approach or a better API integration.

It is not currently required because Open Detail already saves meaningful time.

---

# 25. Staging cleanup

Staging files live under local app data.

The app:

- automatically cleans staging files older than 24 hours on startup;
- includes a manual “Clean Staging Files” button.

Staging files are disposable.

---

# 26. Current UI

Current UI is a browser opened against a local HTTP server:

`127.0.0.1:8768`

The app is local-only.

Current major components:

- top search bar;
- thumbnail size slider;
- Refresh Index;
- left sidebar:
  - selected library path;
  - source `.layout` file list;
  - thumbnail render controls;
  - staging cleanup;
- result cards;
- modal detail inspector;
- Open Detail;
- Open Master LayOut;
- Open SketchUp Source.

The UI screenshot included in this handoff is:

`REFERENCE_UI/full_library_ui_screenshot.png`

---

# 27. Current UI issues / next cleanup

The full company library made UI weaknesses obvious.

## Sidebar

The sidebar lists many individual master `.layout` files.

With ~180 masters this becomes cumbersome and recreates the navigation-tree problem Detail Manager was intended to solve.

### Desired direction

- collapse/hide source-file tree by default;
- use useful filters/categories rather than presenting every file;
- retain source-file filtering as an advanced option.

## Result cards

Cards currently show too much metadata.

User preference:

Main grid should primarily show:

1. large visual thumbnail;
2. intended title;
3. perhaps one short secondary descriptor.

Everything else should move into the selected-detail inspector/modal.

## Detail inspector

The modal is the correct place to show:

- source LayOut;
- page;
- all scenes;
- viewport count;
- exact SketchUp paths;
- raw/clean metadata;
- other technical source data.

---

# 28. Open SketchUp Source — current and future

Current behavior:

- opens the first indexed SketchUp path with `os.startfile`;
- SketchUp opens to whatever scene/view the file was last saved in.

Desired feature:

### Single-scene detail

Open SketchUp model directly to that indexed scene.

### Multi-scene detail

Prompt the user to choose among the associated scenes, or display separate scene buttons in the detail inspector.

Relevant indexed data already exists:

- `scene_name`
- `scene_pid`

Likely future implementation:

- small SketchUp Ruby helper/extension;
- open/load model;
- identify desired scene;
- use `model.pages.selected_page = page`.

Persistent scene IDs should be considered where useful.

This is a high-priority post-UI-cleanup feature.

---

# 29. Full-library validation

This is important: the system has already been tested beyond toy samples.

## Full company library

The user indexed/rendered the **entire LayOut library**.

Result:

- no crashes;
- completed the entire library;
- spot tests behaved as expected;
- subsequently used in production;
- saves time.

This is the strongest validation of the architecture.

## Distribution Library

There is also a smaller “Distribution Library”:

- roughly one third the size;
- stored under a C: path;
- its LayOut/SKP paths were already correctly prepared for that environment.

This version was indexed/rendered on a separate presentation computer.

Result:

- installation worked;
- C: library worked;
- no real issues observed.

So current prototype has been validated on:

1. large mapped/server company library;
2. smaller independent C:-based library on another workstation.

---

# 30. Presentation Prototype 0.1 deployment

The current presentation package is included under:

`PACKAGE_ARCHIVES/Detail_Manager_Prototype_0_1_Presentation.zip`

It includes:

- `detail_manager.py`
- `thumbnail_worker.rb`
- `abbreviations.json`
- `requirements.txt`
- setup BAT
- VBS no-console launcher
- console troubleshooting launcher
- verification BAT
- setup guide.

Current prerequisite approach:

- Windows
- Python 3.12+
- pip
- Tkinter
- PyMuPDF
- SketchUp/LayOut
- browser

The setup BAT installs/checks PyMuPDF and creates a desktop shortcut.

The normal launcher uses `pyw.exe` through VBS so no console remains visible.

### Important

This is a working prototype deployment, **not yet a true standalone compiled installer**.

A future company installer should likely package Python/runtime so ordinary users do not install Python manually.

---

# 31. Company deployment direction

The user agreed with **Option B**:

> one authoritative company index/cache build, many local consumer copies.

Do **not** place one actively used SQLite DB on a network share and have every workstation query/write it directly.

Preferred architecture:

```text
Authoritative Company Detail Library
    |
    +-- master .layout
    +-- master .skp
    |
    v
Designated Index/Publish Machine
    |
    +-- canonical detail index
    +-- thumbnail cache
    +-- abbreviations/config
    +-- version/manifest
    |
    v
Mirrored Company Server Locations
    |
    v
Each Workstation
    |
    +-- local Detail Manager app
    +-- local SQLite DB copy
    +-- local thumbnail/cache copy
    +-- opens master files from shared mapped path
```

Mirrored server drives are acceptable if logical paths are consistent.

Future installation should distinguish:

- administrator/library-maintenance functions;
- normal end-user functions.

Normal users should not need to index/render the entire library.

---

# 32. Future deployment features

Suggested future company deployment features:

- centrally published database/cache;
- version/manifest;
- “library update available” detection;
- local copy/sync of new index/cache;
- shared master library remains authoritative;
- local search remains fast/offloads server;
- diagnostics for missing/unreachable library;
- separate library profiles:
  - Company Library
  - Distribution Library
  - Custom
- configured library root.

Potential internal improvement:

Store Detail Manager’s own master path as:

```text
library_root + relative_path
```

instead of only absolute paths.

This would improve Detail Manager database portability.

**This does not mean changing any path inside the LayOut files.**

---

# 33. Incremental updates

Current indexing already skips unchanged masters based on:

- size;
- mtime_ns.

Future productionization should formalize:

- changed masters only;
- new masters;
- removed masters;
- failed masters;
- incremental thumbnail regeneration only for changed/new masters.

Current code already deletes the full-preview/render cache for a changed master, which is a useful foundation.

---

# 34. Thumbnail maintenance UX

Current process requires:

1. Prepare Render Queue in Detail Manager.
2. Open SketchUp Ruby Console.
3. `load '.../thumbnail_worker.rb'`
4. Return to Detail Manager.
5. Process Rendered Thumbnails.

This is acceptable for development/admin use, but not ideal for broad deployment.

Future:

- install a small SketchUp extension/helper;
- provide an obvious “Run Detail Manager Thumbnail Queue” command;
- or automate the maintenance task through a robust supported mechanism.

This should remain an **administrator task**, not part of daily user workflow.

---

# 35. Diagnostics / status

A future administration/status screen should show:

- current library path;
- application version;
- database version;
- last refresh;
- master count;
- detail count;
- thumbnail count;
- cache size;
- failed masters;
- missing references;
- queued thumbnail renders;
- last render result;
- update availability.

The 07C experiment exposed a UX weakness:

processing warnings were often only surfaced as a temporary toast count.

Persistent diagnostic logs would be better.

---

# 36. Master SketchUp dependency tracking

This is a major future feature.

Goal:

Build relationship:

```text
SKP source
    -> master LayOut files
        -> indexed detail records
```

When a master SKP changes, Detail Manager should be able to answer:

- Which master LayOut files reference it?
- Which details are affected?
- Which references are stale?
- What needs to be reviewed/updated?

Current DB already stores:

- SKP reference IDs;
- exact external paths;
- detail-to-viewport relationships.

This is therefore a logical future module.

---

# 37. Master reference maintenance

Separate from searching.

Future explicit maintenance workflow could help update stale master LayOut references after a master SKP changes.

Rules:

- never silently relink;
- never rewrite paths automatically without explicit maintenance action;
- operate carefully around shared/mirrored network files;
- consider locks/multiple users;
- always preserve exact path behavior unless a human intentionally changes it.

The public LayOut API does not expose a simple obvious Reference Manager “update all references” workflow, so this requires targeted prototyping.

---

# 38. Job Archive Search — future feature

New idea explicitly added to roadmap.

Problem:

Many useful details are drawn for actual jobs but never make it into the formal detail library because there is not enough time to curate/promote them.

Goal:

Make historical job details searchable as a **secondary corpus**.

## Concept

Two sources:

### Curated Library

- trusted;
- standard;
- primary ranking.

### Job Archive

- historical/project-specific;
- useful but not necessarily standard;
- clearly labeled.

Possible UI:

```text
Library | Job Archive | Both
```

or rank:

1. Library
2. Job Archive

Job archive results should have an obvious badge such as:

`JOB ARCHIVE`

## Possible indexing approach

### Best case

Parse historical project `.layout` files directly, using similar group/viewport logic where possible.

This may let the system recover individual details natively.

### Fallback

Export completed job detail sheets to PDF and associate source metadata such as:

- project/job number;
- project name;
- original LayOut file path;
- sheet/page;
- export date.

Varying PDF page sizes are not a major technical issue; PDF pages carry their own dimensions.

The harder problem is automatically identifying individual details within arbitrary job sheets.

Therefore use:

- native project LayOut detail-level parsing when possible;
- PDF/sheet-level fallback otherwise.

## Future “Promote to Library”

When a useful job-only detail is discovered:

- flag it as a candidate;
- put it into a review queue;
- later clean/promote it to the formal library.

This directly attacks the underlying problem of good details being lost in project history.

---

# 39. Visual similarity / SketchUp-context search

Longer-term experimental feature.

Concept:

- user takes/selects a SketchUp view or screenshot;
- Detail Manager ranks visually similar details.

The preferred direction is **not** simple image matching alone.

Potential ranking should combine:

- visual similarity;
- SketchUp model/context information;
- geometry/context clues;
- metadata;
- titles/scenes.

The future Job Archive corpus would make this substantially more valuable because the searchable universe becomes larger than the curated library.

Not a near-term priority.

---

# 40. Search/result workflow ideas

Lower-priority ideas discussed:

- favorites/recently used details;
- a “detail basket” or selected-detail collection;
- smarter search ranking;
- filter categories;
- potentially direct insertion into LayOut.

Do not prioritize these ahead of the known UI cleanup and deployment/admin work unless actual users request them.

---

# 41. What currently DOES NOT work / known limitations

## Not a standalone executable

Current app requires Python/runtime.

Presentation setup works, but final company deployment should be cleaner.

## Browser GUI

Current app runs as a localhost web interface.

This is functional and stable, but not yet a native Windows shell/application.

## Sidebar too dense

Full library makes the source-file list cumbersome.

## Cards too dense

Too much metadata is shown in the main result view.

## Metadata includes noise

Isolated bubble numbers are extracted.

## Full thumbnail crop is not perfect

Stable 07A crop can include small slivers of adjacent sheet content.

It is currently considered good enough.

## Manual Ruby-console render step

Admin workflow only; should eventually be simplified.

## Open SketchUp does not activate indexed scene

Future helper needed.

## No central index publishing/update mechanism

Deployment architecture agreed, not implemented.

## No master dependency-management UI

Data foundation exists, feature not implemented.

## No Job Archive Search

Roadmap only.

## Search returns max 80 results

Current hard-coded search limit is 80. Consider pagination/virtualization later if necessary.

---

# 42. Current HTTP/API endpoints

Current local server handles approximately:

## GET

- `/`
- `/api/status`
- `/api/thumbnail-status`
- `/api/index-status`
- `/api/search`
- `/cache/...`
- `/fullcache/...`

## POST

- `/api/choose-library`
- `/api/index`
- `/api/prepare-thumbnails`
- `/api/process-thumbnails`
- `/api/open-detail`
- `/api/open-master`
- `/api/open-skp`
- `/api/cleanup`

The server binds only to:

`127.0.0.1`

This is intentional.

---

# 43. Open Master / Open SKP behavior

`Open Master LayOut`

- directly opens the indexed `layout_file`.

`Open SketchUp Source`

- JSON-decodes `skp_paths_exact`;
- opens the first indexed path;
- current implementation does not choose a scene.

Windows opening is via:

`os.startfile(...)`

Mapped drive spelling is preserved.

---

# 44. Important staging validation history

## POC 03A

Used LayOut API to clone/template a master, then removed unwanted content.

It worked visually but:

- staging inherited newer LayOut API/version when created from newer installed software;
- produced compatibility warning in LayOut 2025;
- initial staging retained too many caches and stayed ~37.63 MiB.

## POC 03B

Pruned unused image/vector cache data from disposable staging.

Result:

- ~37.63 MiB → ~11.63 MiB;
- ~69.1% reduction;
- SKP reference count unchanged;
- exact external path unchanged;
- embedded SKP hash unchanged.

See:

`REFERENCE_REPORTS/POC03B_TRIM_REPORT.txt`

## POC 03C

Direct 2025-native ZIP/XML staging.

Result:

- version metadata preserved;
- no newer-version warning;
- ~11.63 MiB staging;
- exact path preserved;
- embedded SKP hash preserved.

This became the basis for current stable `build_staging`.

---

# 45. XML serialization lesson

An early POC 05 staging writer used Python `ElementTree` serialization.

LayOut reported “Error reading LayOut file.”

Cause:

ElementTree changed namespace prefix/default-namespace structure enough that LayOut disliked the result.

Stable staging uses `xml.dom.minidom` and tries to preserve the original namespace/prefix structure.

**Do not casually rewrite staging XML using generic serialization.**

This is a major compatibility lesson.

---

# 46. Read-only master policy

Normal operations must treat authoritative masters as read-only.

Indexer:

- opens ZIP for reading.

Staging:

- reads master;
- writes disposable local output.

Thumbnail worker:

- opens master through LayOut API;
- changes layer visibility only in memory;
- exports;
- restores;
- does not save.

Any future master-maintenance module should be clearly separated from ordinary search/index operations.

---

# 47. Multiple users / network considerations

Company masters live on mapped/server drives and may be used by multiple employees.

Future maintenance features must account for:

- file locks;
- someone having a master open;
- mirrored server state;
- partial synchronization;
- explicit write operations only.

Normal Detail Manager searching should remain local/read-only and should not introduce network locks.

---

# 48. Recommended immediate next development phase

The user has already proven the application saves time.

The recommended next release should be a **UI/data cleanup release**, not an architecture rewrite.

Suggested order:

## Prototype 0.2 — UI/data cleanup

1. Simplify/collapse left sidebar.
2. Reduce result-card metadata.
3. Improve detail inspector/modal.
4. Implement raw/clean/display metadata layers.
5. Filter isolated bubble-number callouts from clean/search/display metadata.
6. Improve title/search weighting as needed.
7. Implement Open SketchUp to exact scene:
   - direct for one scene;
   - prompt/buttons for multi-scene.

## Then — deployment/admin

1. central published index/cache;
2. local workstation copies;
3. version/manifest/update mechanism;
4. incremental thumbnail maintenance;
5. admin/status diagnostics;
6. installer/runtime packaging;
7. short User Guide;
8. separate Installation/Admin Guide.

## Then — library intelligence

1. SKP dependency tracking;
2. controlled master reference maintenance;
3. Job Archive Search;
4. Promote to Library;
5. visual/context-assisted search.

---

# 49. Suggested regression tests before every release

Do not make significant changes without repeating core regression checks.

## Indexing

- full library or representative large corpus;
- unchanged master skip;
- changed master reindex;
- deleted master removal;
- malformed/broken master does not crash whole run.

## Detection

- one-viewport detail;
- two-viewport detail;
- 5-view detail if available;
- non-detail top-level groups ignored.

## Search

- raw abbreviations;
- expanded terms;
- filename terms;
- scene terms;
- metadata terms.

## Staging

Open representative details from different masters.

Verify:

- staging opens in LayOut 2025;
- exactly one intended detail;
- labels/callouts retained;
- all viewports retained;
- correct scenes;
- copy/paste works.

## Reference integrity

After pasting several details that share a master SKP:

- project should continue to show one shared SKP reference where native LayOut would consolidate it;
- no path rewriting;
- no unwanted duplicate embedded SKPs.

## Thumbnails

- GUIDES hidden;
- full labels/callouts visible;
- stable crop;
- multi-view detail appears as one preview.

## Persistence

- close app;
- restart Windows;
- launch;
- search immediately without rebuilding.

## Deployment

- mapped company library;
- local C: distribution library;
- no server scenario.

---

# 50. Representative historical test files

These were used during development; they are not bundled in this handoff because they are large.

Examples:

- `(03) FLR TO FLR HYD EXT SJ STD (New Details!).layout`
- `(03) FLR TO FLR HYD EXT SJ STD (New Details!) 2025 Version.layout`
- `(07) FLR TO STL BEAM TRAD BEAR INT SJ.layout`
- `(10) ROOF RDGE TRAD SOLD RFTR.layout`
- `(13) ZE STD KING STUD.layout`
- `TEST 0.layout` through `TEST 5.layout`

Use current company/distribution library files for future real tests rather than relying only on these samples.

---

# 51. Current stable source hashes

Use these if there is any uncertainty about which files are the canonical handoff source.

```text
detail_manager.py
d52bee81b881ac9816d64e2dbd522bf631c740a12d59722205548554f90896e9

thumbnail_worker.rb
265d9fb5228ad0a077c1d5ba1f561cdb67a7242899e0dccc24e3e1a26545f24e

abbreviations.json
1c74957c26f59c0bd8bcf9424d50132900e2f847004d54d9af14c17dd623d976
```

---

# 52. Claude Code operating instructions

If continuing this project:

1. **Read this file fully before modifying code.**
2. Start with `CURRENT_STABLE_SOURCE/detail_manager.py`.
3. Treat current stable behavior as regression-protected.
4. Do not redesign architecture merely because the code is currently one Python file.
5. If refactoring:
   - first create tests/fixtures around parsing, DB, staging, and search;
   - preserve behavior before splitting modules.
6. Never modify authoritative master `.layout` / `.skp` files during routine operations.
7. Never rewrite reference paths.
8. Preserve native copy/paste SKP consolidation.
9. Do not use AutoHotkey.
10. Do not reintroduce the failed API crop experiments as a “fix.”
11. Prefer small incremental changes with repeatable tests.
12. Preserve LayOut 2025 compatibility.
13. Keep 1–5+ viewport details grouped as one logical detail.
14. Any new setup feature should be tested on:
    - company mapped library;
    - C: Distribution Library.
15. When changing XML staging, validate the generated `.layout` package and actually open it in LayOut 2025.

---

# 53. Recommended first Claude task

Do **not** immediately add the largest future feature.

A good first task is:

> Create a clean development repository from the current stable single-file prototype, add regression tests around existing behavior, and implement the first UI/data-cleanup increment without changing indexing/staging semantics.

Specifically:

1. snapshot current source;
2. create tests for:
   - abbreviation expansion;
   - detail detection from representative `.layout` fixtures;
   - multi-viewport grouping;
   - staging validation;
   - search;
3. add a persistent diagnostics/log mechanism;
4. then simplify cards/sidebar and clean metadata.

This establishes a safer foundation before dependency tracking or Job Archive Search.

---

# 54. Product goal in one sentence

**Detail Manager should let an engineer find, inspect, and reuse the right native LayOut/SketchUp detail in seconds, while leaving the authoritative library and its reference structure intact.**
