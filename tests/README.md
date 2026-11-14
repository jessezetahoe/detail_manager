# Tests

Real master files (not committed) go in:

- `tests/fixtures/company/`       - copies of masters from the Z: company library (primary)
- `tests/fixtures/distribution/`  - optional: copies from the C: presentation/Distribution Library

Tests only ever read fixtures and verify they are byte-identical afterwards.

## Running
From `C:\sketchup_dev\detail_manager` (standard library only, no installs):

    py -m unittest discover -s tests

About 40 s. Stage every detail instead of a sample (about 2 min):

    set DM_FULL_STAGING=1 && py -m unittest discover -s tests

Tests use a throwaway app-data folder, never your real index.

## Golden snapshots
`tests/golden/*.json` record exactly what the parser extracts from each fixture
(details, viewports, scenes, titles, exact SKP paths, bounds). If a change is
*meant* to alter parser output (e.g. the title fix), regenerate and review the diff:

    py tests\make_golden.py
    git diff tests/golden
