# Legacy POCs — Do Not Use as the New Baseline

The stable baseline is `CURRENT_STABLE_SOURCE/`.

Historical POC sequence:

- POC01: first single-file read-only index proof.
- POC02: generalized multi-viewport indexer.
- POC03A: LayOut-API staging; worked, but newer-version warning and oversized caches.
- POC03B: cache trim; validated large staging size reduction.
- POC03C: direct native-version ZIP/XML staging; basis for stable Open Detail.
- POC04: AutoHotkey automation proposal; explicitly rejected.
- POC05: first practical browser GUI.
- POC05B: fixed XML namespace serialization; intended titles/abbreviations.
- POC06/06B: direct image-export attempts; not reliable.
- POC06C: PDF-render thumbnail method; successful.
- POC07: integrated full thumbnails with GUIDES hidden.
- POC07A: first crop adjustment; selected as stable baseline.
- POC07B: tighter crop; did not solve neighboring content.
- POC07C: API entity bounds; local-coordinate/matching issues.
- POC07D: transform attempt; Page#entities/group assumption failed.
- POC07E: root-group/transform attempt; grabbed unrelated text/content.
- Reverted to POC07A stable behavior.
- Prototype 0.1: presentation/deployment packaging of stable POC07A logic.

Do not cherry-pick crop code from 07C–07E without an explicit research reason.
