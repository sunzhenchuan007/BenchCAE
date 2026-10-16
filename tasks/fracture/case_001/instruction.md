# Case 001 — fracture mechanics (physics definition pending)

This task supplies two versions of the same planar CAD geometry:

- `input/fracture_1.dxf`: includes internal partitions intended to aid mesh refinement.
- `input/fracture_2.dxf`: without those internal partitions.

The internal partitions are not prescribed crack paths or material interfaces.
The DXF coordinate system must be preserved. The physical length unit is unknown.

**This case is not currently runnable as a physical problem.** Materials,
thickness, 2D assumption, supports, loads, loading history, fracture law and
initial-crack interpretation have not been provided. Do not invent these or
interpret geometry as an implicit boundary condition. See `problem.yaml` for
explicit null fields. There is no reference solution or confirmed GT.

Once the task owner completes the definition, an agent must implement the
core physical model, discretization, assembly and fracture evolution in code.
Python/NumPy/SciPy, geometry, meshing and plotting tools are allowed. Delegating
the entire solve to commercial CAE, reading private GT, and hardcoding result
tables are not allowed. The numerical method is deliberately not selected yet.

Expected outputs for this case are a complete reaction–displacement history
and initial/propagated crack paths, each as CSV and PNG. Other tasks may declare
different output types and independent verifier implementations.

The current implementation checks the submission interface only. No scientific
metric, threshold or claim of numerical validity has been established.
