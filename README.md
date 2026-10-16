# BenchCAE

An open-source prototype for evaluating AI agents on computational mechanics
tasks: **CAD + physical problem → agent-written solver → numerical artifacts →
case-specific independent verifier**.

Current scope: task packaging, DXF inspection, an execution interface, plotting,
and artifact contract checks. **No scientific metric or solver baseline is
implemented.** Each case may choose its own inputs, output types and verifier.

`fracture/case_001` includes the two supplied DXFs, with and without internal
mesh-refinement partitions. Physical conditions and real Ground Truth have not
been supplied; its status is `blocked_missing_physics`. No FEM/cohesive/phase-field
method has been selected. The runnable smoke example is synthetic interface
data, not a simulation, reference solution or evidence of case validity.

## Quick Start

Python 3.11+; commands below run from the repository root. A checkout is needed
because task data lives outside the installed core package.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe benchcae.py inspect --out results/inspection
.\.venv\Scripts\python.exe benchcae.py check
.\.venv\Scripts\python.exe benchcae.py smoke --out results/smoke
.\.venv\Scripts\python.exe -m pytest -q
```

On Linux/macOS, use `.venv/bin/python` instead. `check` intentionally returns
exit code **2**, listing missing physics. Use a fresh output directory for each
run (`results/smoke-2`, etc.). The smoke command executes a tiny, openly labeled
fixture generator in a fresh directory, renders its tables and checks the
artifact contract. It returns **no scientific score** and uses only trusted
local code. The two PNGs and CSVs are under `results/smoke/output/`.

## Run a submission and inspect its artifacts

The following synthetic example exercises the individual commands. Replace
the problem and source directory with an independently defined ready task
when real physical inputs become available.

```powershell
python benchcae.py prepare --problem examples/smoke_task/problem.yaml --out results/public-bundle
python benchcae.py run --problem examples/smoke_task/problem.yaml --source examples/smoke_submission --entry generate.py --backend local-trusted --out results/manual-smoke
python benchcae.py plot --problem examples/smoke_task/problem.yaml --submission results/manual-smoke/output
python benchcae.py validate --problem examples/smoke_task/problem.yaml --submission results/manual-smoke/output --report results/manual-smoke/contract.json
python benchcae.py verify --submission results/manual-smoke/output --report results/not-configured.json
```

Here and below `python` means the activated virtual-environment interpreter.
The last command deliberately returns `not_configured`, `score: null`, exit 2.
There is no GT to compare against. `validate` success only means the file
contract passed; it does not establish correct units, convergence or physics.

For container execution (Docker Engine required):

```sh
docker build -t benchcae-agent:0.1 -f tasks/fracture/case_001/environment/Dockerfile .
python benchcae.py smoke --backend docker --out results/docker-smoke
# Future ready tasks:
# python benchcae.py run --problem tasks/<domain>/<case>/problem.yaml --source <submission> --out results/run-001
```

`run` defaults to Docker: no network, read-only public task/source mounts,
fresh output directory, CPU/memory/process/time limits, no GT mount. The
`local-trusted` backend has **no filesystem isolation**; use it only for code
you trust, never for adversarial benchmark runs. Docker execution was not
tested on the development machine because Docker is unavailable there.

## Organization

```text
benchcae.py                    Unified CLI
benchcae_core/                 Geometry, runner, artifact checks, rendering
tasks/fracture/case_001/       Public instructions/CAD + evaluator-owned verifier stub
examples/smoke_task/           Explicitly synthetic interface task
examples/smoke_submission/     Fixture generator (not a solver)
baselines/fracture/            Reserved; no baseline implemented
private/ground_truth/          Ignored evaluator-only data, currently empty
results/                      Ignored local run artifacts
tests/                        Framework tests
docs/                         Inspection, architecture and current limitations
```

`prepare` exports only `instruction.md`, `output_contract.md`, `problem.yaml`
and `input/`. It never exports `tests/`, `verifier/`, baselines or private data.
Each case's `problem.yaml` declares outputs and a trusted verifier entry. The
core does not prescribe fracture metrics or force every task to return two plots.

See [inspection](docs/inspection.md), [architecture](docs/architecture.md),
[reference review](docs/references.md), and [contributing](CONTRIBUTING.md).
Original uploads remain untouched. Source is MIT licensed; the supplied CAD
inputs and their provenance are documented in the inspection record.
See [publication hygiene](docs/publication.md) for privacy checks before commits.
