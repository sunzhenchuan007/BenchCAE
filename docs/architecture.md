# Minimal interfaces and trust boundaries

Every case is independently specified by `problem.yaml`. `outputs` is a list,
not two hardcoded filenames in the runner. The generic artifact checker accepts
declared CSV headers and numeric columns, optional PNGs, and metadata. The two
available plotting adapters are optional convenience renderers for the present
fracture output types. Future tasks can provide different tables/renderers.

Task-specific physical completeness uses `required_fields` dotted paths and
an explicit status. Input geometry alone cannot make a real task runnable.
`prepare` can still export an incomplete task for inspection/discussion.

The runner copies public instructions/input and submitted source into a new
run directory, then starts the entry with `--problem` and `--output`. Run
directories cannot be reused. It records input/source SHA-256 hashes, command,
exit status, backend and time limit in `run.json`, with stdout/stderr in a log.
Nonzero exits and timeouts do not count as successful executions. Process-tree
termination is implemented for local timeouts; Docker cleanup removes the named
container. This MVP does not implement a model-provider or conversational agent
loop: it executes code produced by an agent, not an LLM API.

Docker receives only `/task`, `/source` and `/output`; it does not receive the
repository root, verifier, reference solution or private GT. It runs without
network or capabilities, as a non-root user, with a read-only root and bounded
resources. Docker must be installed and its daemon available; the supplied
image recipe and backend need validation on a Docker-capable host. A local
subprocess offers no security boundary or protection against hostile code.

Independent verification is a second command. `verify` resolves the entry from
the trusted task configuration (never from submission metadata). GT is an
argument only to this evaluator process, not to the runner. Metric selection,
formulas, coordinate transformations, reference provenance, convergence checks
and threshold calibration belong to each case. All are deferred for case_001.

`validate` is deliberately separate: it tests a file contract and returns
`score: null`, `physics_validated: false`. A valid PNG or an exit code of zero
cannot establish that a simulation occurred. Source auditing, reruns, hidden
physical variations and scientifically justified verifiers remain future work.

Private paths and results are ignored by Git. This prevents accidental normal
adds but does not prevent forced adds or local filesystem access. Formal runs
must use isolated environments and evaluator-controlled immutable artifacts.

Current limits: DXF XY only (STEP explicitly rejected), no mesher, no physics
solver, no GT, no scientific metrics, no provider integration, no leaderboard,
no website or deployment. The synthetic fixture tests file/CLI plumbing only.
