# Chip review: how each chip is read from the real names

Built 2026-11-22 from the full library index (5,254 details) plus the Non-Library job files.
For each group: every way its codes are written in the SketchUp scene names, how many views
use that pattern, which chips it switches on, and an example. Either-or groups (Joist, Floor
system, Beam, Joist at beam, Location) take the master FILE NAME first; the last section shows
where their chips came from.

## Questions for you (my default in brackets)
1. **Joist direction, "Pa Hang 2 Pe Top" style** (131 views): one side parallel and hung, the
   other perpendicular and sitting on top. Today it switches on BOTH Parallel and Perpendicular.
   Should it count as "Para -> Perp" (and "Pe Hang 2 Pa Top" as "Perp -> Para")? [yes]
2. **Roof: "Roof Abv" vs "Roof Even"** (1,008 views each): today both are "Roof outside", and
   "Roof Even" also switches on "Even elevation". Split into "Roof above" and "Roof even"? [yes]
3. **Flush from scene names** (headers "2 Ply Hdr Flush", beam pockets "Bm Pkt Flush One Side"):
   only matters where the file name has no FLSH/BEAR. Keep, or take Flush from file names only?
   [file names only: in scenes it means header/pocket flush, not joists flush to a beam]
4. **Location from scene names**: edge nailing details with views "Ext" and "Int" get both
   Exterior and Interior. Fine? [fine]
5. Anything in the tables below that reads wrong.


## Joist (either-or)


**Library** (3 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 1356 | TJI | I-Joist | TJI Para NW ABV Hyd |
| 1008 | SJ | Solid Joist | Pa2Pa 2 Ply Bm Wall Abv SJ Roof Abv Shear Hyd |
| 145 | TJI TJI | I-Joist | TJI Pa2Pe TJI Roof Hyd |

**Non-Library (jobs)** (2 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 63 | TJI | I-Joist | TJI Para Hyd |
| 7 | SJ | Solid Joist | Pe2Pe Wd Bm Wall Abv SJ Roof Abv Shear Hyd |

## Floor system (either-or)


**Library** (1 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 2575 | HYD | Hydronics | Pa Hang Hyd |

**Non-Library (jobs)** (1 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 99 | HYD | Hydronics | CMST HEDR BLW HYD |

## Beam (either-or)


**Library** (1 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 784 | STL | Steel | Pa Stl Bm Nail Hyd |

**Non-Library (jobs)** (1 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 42 | STL | Steel | Pe Stl Bm Hyd |

## Joist at beam (either-or)


**Library** (2 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 19 | FLUSH | Flush | 2 Ply Hdr Flush |
| 16 | FLSH | Flush | CMST HEDR FLSH HYD |

**Non-Library (jobs)** (2 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 45 | FLUSH | Flush | Bm Pkt Flush One Side |
| 3 | FLSH | Flush | CMST HEDR FLSH HYD |

## Location (either-or)


**Library** (2 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 206 | INT | Interior | Stem Conc. w/ Wall Int Slab |
| 8 | EXT | Exterior | EN Shr Dbl Sided Ext |

**Non-Library (jobs)** (2 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 38 | EXT | Exterior | EN Shr One Sided Ext |
| 36 | INT | Interior | Stem Conc. w/ Wall Int Slab |

## Wall


**Library** (14 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 1050 | WALL ABV | No wall below, Wall above | Pa 2 Ply Bm Wall Abv Hyd |
| 756 | WALL ABV BLW | Wall above, Wall below | Pa 2 Ply Bm Wall Abv Blw Shear Hyd |
| 504 | WALL ABV ABV | No wall below, Wall above | Pa2Pa 2 Ply Bm Wall Abv SJ Roof Abv Shear Hyd |
| 504 | WALL ABV BLW ABV | Wall above, Wall below | Pa2Pa 2 Ply Bm Wall Abv Blw SJ Roof Abv Shear Hyd |
| 312 | WALL BLW | No wall above, Wall below | Pa 2 Ply Bm Wall Blw Hyd |
| 144 | NW | No wall | Pa Top Cont NW Hyd |
| 44 | WALL | - | Stem Conc. w/ Wall Int Slab |
| 36 | NO WALL | No wall | TJI Pa Cont Hyd No Wall |
| 24 | NW ABV | No wall above | TJI Para NW ABV Hyd |
| 22 | BLW | - | Grade Beam Blw Frame |
| 12 | NO | - | STD Mid - No Bolts |
| 4 | BLW WALL | - | Solid Pa2Pa Blw Wall Rim |
| 4 | ABV | - | Pe2Pa Abv |
| 4 | ABV BLW | - | HD Abv & Blw 2 Ply Bm |

**Non-Library (jobs)** (12 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 91 | WALL | - | Stem Conc. w/ Wall Perf |
| 24 | WALL ABV | No wall below, Wall above | Pe Stl Bm Wall Abv Hyd |
| 16 | NO WALL | No wall | TJI Pe Cont Hyd No Wall |
| 6 | NW ABV | No wall above | TJI Perp NW ABV Hyd |
| 5 | BLW | - | CMST HEDR BLW HYD |
| 4 | WALL ABV ABV | No wall below, Wall above | Pe2Pe Wd Bm Wall Abv SJ Roof Abv Shear Hyd |
| 4 | NO | - | STD Mid - No Bolts |
| 3 | WALL BLW | No wall above, Wall below | Pa Stl Bm Nail Wall Blw Hyd |
| 3 | ABV | - | Pe2Pa Abv |
| 3 | NW | No wall | Pe Top Cont NW Hyd |
| 2 | WALL ABV BLW | Wall above, Wall below | Pe 2 Ply Bm Int Wall Abv Blw Shear |
| 1 | ABV BLW | - | HSS Abv / Blw |

## Joist direction


**Library** (12 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 1167 | PE2PA | Perp → Para | Pe2Pa Top Hyd Ins |
| 1022 | PE2PE | Perp → Perp | Pe2Pe Top Pony Hyd |
| 989 | PE | Perpendicular | Pe Hang Hyd |
| 667 | PA | Parallel | Pa Hang Hyd |
| 604 | PA2PA | Para → Para | Pa2Pa Top Pony Hyd |
| 411 | PA2PE | Para → Perp | TJI Pa2Pe Deck - Hyd |
| 68 | PE PE | Perpendicular | Pe Hang 2 Pe Top Hyd Ins |
| 66 | PA PA | Parallel | Pa Hang 2 Pa Top Hyd |
| 66 | PA PE | Parallel, Perpendicular | Pa Hang 2 Pe Top Hyd Ins |
| 65 | PE PA | Parallel, Perpendicular | Pe Hang 2 Pa Top Hyd Ins |
| 26 | PERP | Perpendicular | TJI Perp NW ABV Hyd |
| 24 | PARA | Parallel | TJI Para NW ABV Hyd |

**Non-Library (jobs)** (10 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 74 | PE | Perpendicular | Pe Stl Bm Hyd |
| 44 | PE2PA | Perp → Para | Pe2Pa Wd Bm Hyd |
| 32 | PE2PE | Perp → Perp | Pe2Pe Stl Bm Nail Hang Wall Abv Hyd |
| 32 | PA | Parallel | Pa 2 Ply Bm Wall Abv Shear |
| 23 | PA2PA | Para → Para | Pa2Pa Stl Bm Hyd |
| 16 | PERP | Perpendicular | TJI Perp Hyd |
| 14 | PARA | Parallel | TJI Para Hyd |
| 4 | PA2PE | Para → Perp | TJI Pa2Pe Roof - Hyd |
| 1 | PE PE | Perpendicular | TJI Pe Hang Slp Fm Pe Slab Drv |
| 1 | PA PE | Parallel, Perpendicular | TJI Pa Hang Slp Fm Pe Slab |

## Foundation


**Library** (16 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 228 | RET | Retaining | Pa Hang Hyd Ret |
| 144 | INS RET | Insulation, Retaining | Pa Hang Hyd Ins Ret |
| 138 | INS | Insulation | Pa Hang Hyd Ins |
| 120 | PONY | Pony wall | Pa Top Pony Hyd |
| 120 | PONY RET | Pony wall, Retaining | Pa Top Pony Hyd Ret |
| 49 | SLAB | Slab | HSS w/ Slab |
| 48 | SLAB RET | Retaining, Slab | Pa Hang Slab Hyd Ret |
| 30 | CMU | CMU | HSS 2 Side Bolt 1 Side Nailer CMU Shear |
| 24 | SLAB INS | Insulation, Slab | Pa Hang Slab Hyd Ins |
| 24 | SLAB INS RET | Insulation, Retaining, Slab | Pa Hang Slab Hyd Ins Ret |
| 10 | STEM CMU | CMU, Stem | Stem CMU |
| 10 | STEM CONC | Concrete, Stem | Stem Conc. |
| 5 | CONC | Concrete | Custom CBQ Conc. |
| 4 | STEM CONC SLAB | Concrete, Slab, Stem | Stem Conc. w/ Wall Int Slab |
| 2 | STEM CMU SLAB | CMU, Slab, Stem | Stem CMU w/ Wall Slab |
| 1 | STEM | Stem | ICOL w/ Stem |

**Non-Library (jobs)** (11 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 53 | STEM CONC | Concrete, Stem | Stem Conc. Perf |
| 22 | SLAB | Slab | Slab Toe |
| 15 | PONY | Pony wall | Pa Top Pony Hyd |
| 11 | STEM CONC SLAB | Concrete, Slab, Stem | Stem Conc. w/ Wall Perf Slab |
| 10 | CONC | Concrete | Iso Pedestal Conc. |
| 6 | RET | Retaining | Pa Top Hyd Ret |
| 5 | PONY RET | Pony wall, Retaining | Pa Top Pony Hyd Ret |
| 2 | SLAB RET | Retaining, Slab | Pe Hang Slab Hyd Ret |
| 2 | STEM CMU | CMU, Stem | Stem Step at Shear Wall CMU |
| 1 | STEM | Stem | ICOL w/ Stem |
| 1 | CMU | CMU | Custom CBQ CMU |

## Other


**Library** (21 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 709 | TOP | Sits on top (not hung) | Pa Top Pony Hyd |
| 672 | ABV ROOF ABV | Roof outside | Pa2Pa 2 Ply Bm Wall Abv SJ Roof Abv Shear Hyd |
| 672 | ABV ROOF EVEN | Even elevation, Roof outside | Pa2Pa 2 Ply Bm Wall Abv Blw SJ Roof Even Shear Hyd |
| 566 | ABV | - | TJI Para NW ABV Hyd |
| 336 | SKEW ABV ROOF ABV | Roof outside, Skewed | Pe2Pa 2 Ply Bm Skew Wall Abv Blw SJ Roof Abv Shear Hyd |
| 336 | SKEW ABV ROOF EVEN | Even elevation, Roof outside, Skewed | Pe2Pa 2 Ply Bm Skew Wall Abv SJ Roof Even Shear Hyd |
| 252 | SKEW ABV | Skewed | Pe 2 Ply Bm Skew Wall Abv Hyd |
| 240 | TOP CONT | Continuous, Sits on top (not hung) | Pa Top Cont NW Hyd |
| 228 | SKEW | Skewed | Pe 2 Ply Bm Skew Hang Hyd |
| 149 | ROOF | Roof outside | TJI Pa2Pe Roof - Hyd |
| 72 | ROOF WSW | Roof outside, Strong Wall | TJI Pa2Pe Roof WSW Hyd |
| 50 | DECK SE | Deck, Sealed | TJI Pa2Pe Deck Se - Hyd |
| 48 | DECK SE WSW | Deck, Sealed, Strong Wall | TJI Pa2Pe Deck Se WSW Hyd |
| 34 | CONT | Continuous | TJI Pa Cont Hyd No Wall |
| 26 | DECK | Deck | TJI Pa2Pe Deck - Hyd |
| 24 | WSW | Strong Wall | TJI Para Hyd WSW |
| 24 | DECK WSW | Deck, Strong Wall | TJI Pa2Pe Deck WSW Hyd |
| 24 | CONT WSW | Continuous, Strong Wall | TJI Pa Cont Hyd WSW |
| 12 | ABV WSW | Strong Wall | TJI Para NW ABV HYD WSW |
| 5 | KP | Knife plate | WCOL KP CMU |
| 1 | CONT CONT | Continuous | Pa2Pa Cont Wall Cont |

**Non-Library (jobs)** (9 patterns)

| Views | Pattern | Chips | Example scene |
|---:|---|---|---|
| 39 | TOP | Sits on top (not hung) | Pa Top Pony Hyd Ret |
| 33 | ABV | - | Pe Stl Bm Wall Abv Hyd |
| 19 | CONT | Continuous | TJI Pe Cont |
| 9 | TOP CONT | Continuous, Sits on top (not hung) | Pe Top Cont Hyd Ret |
| 5 | ROOF | Roof outside | TJI Pe2Pa Roof - Hyd |
| 4 | ABV ROOF ABV | Roof outside | Pe2Pe Wd Bm Wall Abv SJ Roof Abv Shear Hyd |
| 3 | DECK SE | Deck, Sealed | TJI Pe2Pe Deck Se |
| 3 | ABV ROOF EVEN | Even elevation, Roof outside | Pa2Pe Stl Bm Wall Abv SJ Roof Even Hyd |
| 1 | KP | Knife plate | KP - 1" Bolts |

## Either-or groups: where the chip came from (details)


**Joist**

| Source | From | Details | Example |
|---|---|---:|---|
| library | file: I-Joist | 1687 | (02) FLR TO FND CMU HYD TJI.layout / Pa Hang Hyd |
| library | file: Solid Joist | 1684 | (02) FLR TO FND CMU HYD SJ.layout / Pa Hang Hyd |
| library | file: Truss Joist | 1675 | (02) FLR TO FND CMU HYD TJ.layout / Pa Hang Hyd |
| library | none | 208 | (01) FND CMU CONT.layout / Grade Beam at Garage |
| projects | none | 1074 | 1791 S0.1.layout / Stem Conc. Perf |
| projects | scene: I-Joist | 50 | 1791 S0.11.layout / TJI Para Hyd |
| projects | scene: Solid Joist | 7 | 1791 S0.14.layout / Pe2Pe Wd Bm Wall Abv SJ Roof Abv Shear Hyd |

**Floor system**

| Source | From | Details | Example |
|---|---|---:|---|
| library | file: Hydronics | 2526 | (02) FLR TO FND CMU HYD SJ.layout / Pa Hang Hyd |
| library | file: Traditional | 2581 | (02) FLR TO FND CMU TRAD SJ.layout / Pa Hang |
| library | none | 147 | (01) FND CMU CONT.layout / Grade Beam at Garage |
| projects | none | 1065 | 1791 S0.1.layout / Stem Conc. Perf |
| projects | scene: Hydronics | 66 | 1791 S0.11.layout / CMST HEDR BLW HYD |

**Beam**

| Source | From | Details | Example |
|---|---|---:|---|
| library | file: Double ply | 918 | (04) FLR TO 2PLY BEAM HYD FLSH EXT SJ (New De / Pa2Pa 2 Ply Bm Wall Abv SJ Roof Abv Shear Hyd |
| library | file: Solid | 994 | (04) FLR TO SOLD BEAM HYD FLSH EXT SJ (New De / TJI Pa Wd Bm Pa Solid Roof Hyd |
| library | file: Steel | 830 | (04) FLR TO STL BEAM HYD FLSH EXT SJ.layout / Scene 107 |
| library | file: Triple ply | 918 | (04) FLR TO 3PLY BEAM HYD FLSH EXT SJ (New De / Pa2Pa 3 Ply Bm Wall Abv SJ Roof Abv Shear Hyd |
| library | none | 1590 | (01) FND CMU CONT.layout / Grade Beam at Garage |
| library | scene: Steel | 4 | (08) ROOF EAVE TRAD TJI RFTR.layout / TJI Pe Evs Stl Bm |
| projects | none | 1098 | 1791 S0.1.layout / Stem Conc. Perf |
| projects | scene: Steel | 33 | 1791 S0.11.layout / Pe Stl Bm Hyd |

**Joist at beam**

| Source | From | Details | Example |
|---|---|---:|---|
| library | file: Bearing | 1728 | (06) FLR TO 2PLY BEAM HYD BEAR EXT SJ (New De / Pa2Pa 2 Ply Bm Wall Abv SJ Roof Abv Hyd |
| library | file: Flush | 1881 | (04) FLR TO 2PLY BEAM HYD FLSH EXT SJ (New De / Pa2Pa 2 Ply Bm Wall Abv SJ Roof Abv Shear Hyd |
| library | none | 1612 | (01) FND CMU CONT.layout / Grade Beam at Garage |
| library | scene: Flush | 33 | (13) ZE STD CMST STRP AT HYD FLR HD (New Deta / CMST HEDR FLSH HYD |
| projects | none | 1098 | 1791 S0.1.layout / Stem Conc. Perf |
| projects | scene: Flush | 33 | 1791 S0.11.layout / CMST HEDR BLW HYD |

**Location**

| Source | From | Details | Example |
|---|---|---:|---|
| library | file: Exterior | 3360 | (03) FLR TO FLR HYD EXT SJ STD (New Details!) / TJI Pa2Pe TJI Roof Hyd |
| library | file: Interior | 666 | (03) FLR TO FLR HYD INT SJ STD.layout / TJI Pe2Pa Hyd No Wall |
| library | none | 1221 | (01) FND CMU CONT.layout / Grade Beam at Garage |
| library | scene: Exterior | 1 | (13) ZE STD EN AT CRNR.layout / EN Shr One Sided Ext |
| library | scene: Exterior+Interior | 4 | (13) ZE STD EN AT CRNR.layout / EN Shr Dbl Sided Int |
| library | scene: Interior | 2 | (01) FND CMU CONT.layout / Stem Conc. w/ Wall Int Slab |
| projects | none | 1103 | 1791 S0.1.layout / Stem Conc. Perf |
| projects | scene: Exterior | 3 | 1852 S2.2.layout / EN Shr One Sided Ext |
| projects | scene: Exterior+Interior | 18 | 1791 S0.5.layout / EN Shr One Sided Ext |
| projects | scene: Interior | 7 | 1791 S0.1.layout / Stem Conc. w/ Wall Int Slab |
