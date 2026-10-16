# Case 001: original-file inspection

Inspected 2026-10-16. The workspace originally contained exactly two DXFs and
no CSV, STEP, material definition, solver model or Ground Truth files.

| Source | Canonical copy | Entities | SHA-256 |
|---|---|---|---|
| 断裂1.dxf | tasks/fracture/case_001/input/fracture_1.dxf | 15 SPLINE + 11 LWPOLYLINE | c6803601e874521f1138c653ea7beac348ebc2db829eba31ee36c2824b85bcd0 |
| 断裂2.dxf | tasks/fracture/case_001/input/fracture_2.dxf | 15 SPLINE + 1 LWPOLYLINE | 5dd25f3f64a74d5ed7986a905cb6f1b8b73faba7095d89a7c4a9bc6cf300f0ad |

Both contain planar XY geometry with bounds `[0, 0]` to `[0.065, 0.12]` in
**unconfirmed CAD units**, not confirmed metres or millimetres. Raw headers say
AC1012. There is no `$INSUNITS` or `$MEASUREMENT` field. All model-space entities
are on layer `0`; no material/BC annotations are present.

Rational quadratic splines describe three circular boundaries, with centers
approximately `(0.020, 0.020)`, `(0.020, 0.100)`, `(0.0365, 0.051)` and radii
`0.005`, `0.005`, `0.010`. The outer profile has a left slot from `x=0` to
`x=0.010`, bounded by `y=0.06475` and `y=0.06525`. These are geometry observations.
They do not establish hole-loading conditions, thickness, an initial sharp
crack, fracture mode, or an intended specimen standard.

The user identified the extra boundaries in fracture_1 as mesh-refinement
partitions. Both originals are preserved; canonical copies have identical
hashes. The reader retains and samples rational curves through ezdxf rather
than joining spline control points as straight segments. Tessellation is for
inspection/rendering only, not a mesh or a validated domain decomposition.

Missing physical inputs are explicit nulls in `problem.yaml`: length unit,
plane stress/strain/3D assumption, thickness, material properties, supports,
loading and increments, initial crack interpretation, fracture law/parameters,
reaction extraction, crack extraction, and convergence requirements. The model
and numerical method remain undecided. No physical solver or metric was built.

Regenerate the inspection report and side-by-side PNG:

```sh
python benchcae.py inspect --out results/inspection
```
