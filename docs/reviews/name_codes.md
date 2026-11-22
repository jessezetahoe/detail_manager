# Name codes in the library (for choosing search chips)

Scanned 2026-11-22 from the index of the full library: 182 masters, 5,254 details.
"Details" = how many details carry the code. Codes come from the master file name (applies
to every detail of that master) or from the detail's SketchUp scene names.

## Proposed chip groups

| Group | Chips (code -> details) | Source |
|---|---|---|
| Joist | Solid Joist `SJ` 1,684 · Truss Joist `TJ` 1,675 · I-Joist `TJI` 1,687 | file name |
| Floor system | Hydronics `HYD` 2,526 · Traditional `TRAD` 2,581 | file name |
| Beam | Double ply `2PLY` 918 · Triple ply `3PLY` 918 · Solid `SOLD` 994 · Steel `STL` 830 | file name (scenes: `Wd` 1,049, `Stl` 783, `Ply` 1,846) |
| Joist at beam | Flush `FLSH` 1,881 · Bearing `BEAR` 1,728 | file name |
| Location | Exterior `EXT` 3,360 · Interior `INT` 666 | file name |
| Wall | Wall above `Abv` 2,822 · Wall below `Blw` 1,586 · No wall `NW` 168 | scene (`Wall` 3,207) |
| Joist direction | `Pa` 840 · `Pe` 1,153 · `Pa2Pa` 604 · `Pa2Pe` 411 · `Pe2Pa` 1,141 · `Pe2Pe` 1,022 | scene |
| Foundation | Concrete `CONC` 541 · CMU `CMU` 536 · Retaining `RET`/`Ret` 504 · Slab 151 · Stem 26 · Insulation `Ins` 330 · Pony wall 240 | file name + scene |
| Connection | Hanger `Hang` 682 · Weld 102 · Bolt(s) 40 · Nail 156 · Strap `STRP` 39 · Holdown `HD` 40 | scene + file name |
| Other | Shear 1,059 · Wood Strong Wall `WSW` 204 · Deck 148 · Roof 2,237 | scene |

## Codes I do not know (please explain)
| Code | Details | Example scene |
|---|---|---|
| `Skew` | 1,152 | (with Pe2Pa / Pe2Pe floor-to-beam details) |
| `Even` | 1,008 | |
| `Top` | 825 | (foundation: "Pa Top Pony Hyd") |
| `Roof` | 2,237 | (inside floor-to-beam scenes) |
| `Cont` | 299 | ("Pa Top Cont Hyd") |
| `Se` | 98 | ("TJI Pa2Pa Deck Se WSW") |
| `Flat`, `Cav`, `Mid`, `KP`, `ICOL` | 50, 6, 6, 5, 5 | |

## Other file-name codes (fewer details)
`STD` 274 · `ROOF`/`RFTR` 52 · `CONN` 46 · `CMST` 30 · `HSS` 26 · `WSP` 23 · `EAVE` 22 · `FRME` 18 ·
`RAKE` 14 · `POST` 13 · `PKT` 11 · `WDP` 10 · `TRSS` 10 · `HEDR` 9 · `RDGE` 6

## Notes
- Chips are taken from names only, never from notes (notes say "wall" and "beam" everywhere).
- Each chip: off (either) / on (must have) / second click (must not have), with live counts.
- Non-Library job details have looser names (often default scene names): fewer chips will apply to them.
