# Submission interface v1 (provisional, not a physical specification)

Entry command:

```sh
python solver.py --problem /task/problem.yaml --output /output
```

Read CAD paths relative to the problem file. Write outputs only to `--output`.
Submit the executable Python source directory separately. `solver.py` may import
helper Python modules in that directory. It must not require GT or network access.
Environment dependencies are declared under `environment/` and installed before
execution. Any additional dependency requires an environment revision.

Required outputs in this case:

| File | Columns / contents |
|---|---|
| reaction_curve.csv | step,segment,displacement,reaction |
| crack_path.csv | path_id,kind,point_index,step,x,y |
| reaction_curve.png | Complete loading history; labeled units |
| crack_path.png | Original CAD with distinct initial and propagated paths |
| metadata.json | Schema, case ID, data kind, units, coordinate frame and solver status |

UTF-8 CSV with the exact declared header and finite numeric cells. Retain row
order and the full loading history. `step` starts at zero; `segment` identifies
loading/unloading branches. A crack's `kind` is `initial` or `propagated`;
`point_index` orders each path and `step` records first appearance. Branched
cracks can use different `path_id` values. The eventual task-specific verifier
will define physical interpretation, extraction and sampling requirements.

Metadata example (unknowns are intentionally not usable physical values):

```json
{
  "schema_version": 1,
  "case_id": "fracture/case_001",
  "data_kind": "real",
  "units": {"length": null, "displacement": null, "reaction": null},
  "coordinate_frame": {"name": "original_cad_xy"},
  "solver": {"status": "not_run"}
}
```

The builtin renderer requires coordinates already in the original CAD XY
frame and CAD length units. Other frames need a task-specific conversion; no
best-fit alignment or inferred scaling is applied. Physical units, force sign,
reaction location and out-of-plane thickness are pending task-owner input.

`validate` checks files, headers, numeric finiteness, PNG decoding and metadata
presence only. It does not verify convergence, physics, crack semantics or
unit correctness. `verify` is the distinct, evaluator-owned scientific extension.
