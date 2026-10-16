# Local delivery record — 2026-10-16

The final scope follows the user's clarification: independent task packaging
and execution interfaces; metrics and solver-based assessment of the physical
problem are deferred. There is no real numerical baseline or scientific score.

## Created

- `benchcae.py`, installable `benchcae_core/`, `pyproject.toml`, MIT license,
  README Quick Start, contribution guide and GitHub Actions test workflow.
- `tasks/fracture/case_001/`: instructions, output contract, incomplete physics
  configuration, two byte-identical copies of the original CADs, environment,
  verifier stub and geometry-input tests.
- `examples/`: a separate synthetic interface task and fixture generator.
- `baselines/fracture/README.md`: explicitly no baseline implementation.
- `private/ground_truth/`: empty except `.gitkeep`, ignored by Git.
- `docs/`: original inspection, architecture, reference review and this record.
- `results/`: inspection JSON/PNG, smoke-run source/input snapshots and logs,
  two CSVs and two PNGs, artifact report, public task bundle and unconfigured
  verifier report. These generated files are ignored by Git.

The original root-level `断裂1.dxf` and `断裂2.dxf` were not changed.
At the initial prototype delivery, Git was initialized on `main` without a
commit or remote. Publication was authorized separately after privacy review.

## Commands actually executed

PowerShell from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe benchcae.py inspect --out results/inspection
.\.venv\Scripts\python.exe benchcae.py prepare --out results/case001_public
.\.venv\Scripts\python.exe benchcae.py smoke --out results/smoke
.\.venv\Scripts\python.exe -m pytest -q
git init -b main
git check-ignore private/ground_truth/example.csv results/smoke/output/reaction_curve.csv .venv/pyvenv.cfg
```

Editable installation succeeded. The first build attempt encountered a Windows
sandbox temporary-directory access error; retry succeeded with process-local
`TEMP` and `TMP` pointing to the workspace's ignored `tmp/pip/`. No global
environment or system Python packages were changed.

`pytest`: **24 passed**, 23.28 seconds on Windows/Python 3.11.5. There were 21
upstream pyparsing deprecation warnings from ezdxf/matplotlib; no test failures.
Coverage includes fresh execution, blocked real tasks, public bundle allowlist,
missing files, malformed/empty CSV, NaN/Inf, invalid PNG, synthetic/real mismatch,
deterministic contract reports, a different task's single unplotted table,
case-specific verifier dispatch, process failure, timeout, path escapes, and
actual CAD hashes/bounds/rational-curve sampling.

The smoke run generated 21 curve rows and 13 path rows. Metadata says
`data_kind: synthetic`, `solver.status: not_run`; the contract report says
`score: null`, `physics_validated: false`. All three generated plots (including
the original CAD comparison) were visually inspected. These plots establish
rendering only, not valid physics or actual crack growth.

Expected blocked/unconfigured commands were also exercised:

```powershell
.\.venv\Scripts\python.exe benchcae.py check
.\.venv\Scripts\python.exe benchcae.py verify --submission results/smoke/output --report results/unconfigured_verifier.json
```

They intentionally return exit code 2, listing missing conditions or
`not_configured` without a score. Git ignore checks confirmed that future
private GT, local results and the virtual environment are excluded.

## Not completed / deliberately deferred

- Scientific metrics and thresholds: left to each case; not implemented.
- Physical model selection, FEM/phase-field/cohesive solver, mesh and convergence
  study: not performed, in accordance with the scope clarification.
- Real material/BC/loading/crack definition and GT: not supplied.
- Docker backend execution: recipe and command construction exist, but Docker
  is unavailable on this machine; no claim of a tested container runtime.
- STEP support: explicit unsupported-format error; DXF XY supported now.
- Actual LLM agent orchestration and remote publication: not implemented.
