# Old Projects check (O1), 2026-11-18

19 job LayOut files from 3 jobs (1757: 14 single-sheet files, LayOut 2022; 1875: 3 files of 4 sheets
and 1926: 2 files of 3 sheets, LayOut 2025). 1.5 GB in total.

| Question | Result |
|---|---|
| Can they be read like the library? | Yes. 567 details found, read in about 4 seconds for all 19 files |
| Are details grouped one per detail? | Yes. No group held two details. 9 SketchUp views (in 2 files) sat outside any group: skipped and listed in Diagnostics |
| Real (drawn) title found? | 540 of 567 with the library rule. In job files the title box sometimes comes AFTER "N.T.S." instead of before; allowing that order (library order still wins) leaves only a handful without a drawn title (steel step views such as "SIDE VIEW", "STEP 1: ..."), which now use their best text instead of "Scene 3" |
| Scene names | 444 of 846 are SketchUp defaults ("Scene 3", "Last saved SketchUp View"). Never used as a title or shown on a card |
| Where do the SketchUp models live? | Mostly the job's own custom models (428 details), then the OLD library location `Z:/Google Drive/ZE Sketchup/ZE Detail Scrapbooks` (95), then the current library (28). So old jobs are mostly custom work: exactly what the library lacks |
| Pasted from the library? | Matched exactly (same model, same scene) to a library detail: 6 against the 8 sample library masters. Against the full library there will be more. Shown as "Same as Library: <title>" |
| Open Detail from a job file | Works. 2 seconds on the largest file (253 MB, local disk); the staging file is about 10 MB |
| Detail numbers | Job details carry their real detail number (801, 1002 ...) beside the title. Not used yet; could be shown later |
| Page size | No issue: each sheet is read as it is |
| Search example | "shower": the library has nothing; Old Projects has the depressed-shower details |
