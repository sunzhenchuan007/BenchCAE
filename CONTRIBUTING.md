# Contributing

Each case is an independent task under `tasks/<domain>/<case>/`. Start with
instructions, an input manifest, `problem.yaml`, public input files and an
explicit output contract. Add or remove required fields to suit the physics;
the core checks dotted paths declared by the task, not a global physics model.

Choose metrics only after the task and available references are established.
Implement scientific verification in that case's evaluator-owned `verifier/`.
The eventual entry accepts `--problem`, `--submission`, `--gt`, and `--report`,
emits JSON, and never executes untrusted submission code with access to GT.
Set `verifier.status: ready` only when it is implemented and tested. The current
stub deliberately reports `not_configured` and no score.

Keep real GT outside the public repository and agent-visible environment. Do
not force-add ignored data. Review `git status --ignored` before publication.
Run `python tools/check_public_files.py --staged` before committing; see
`docs/publication.md` for credential, local-path and commit-attribution rules.
Synthetic fixtures must say synthetic in configuration, metadata and figures;
they cannot validate a physical case. Do not infer materials or loading from CAD.

For actual solver tasks, require executable source and declare allowed numerical
dependencies. Numerical methods, discretization, evolution laws, convergence
evidence and independent references require case-specific scientific review.

Run `python -m pytest -q` after framework changes. Add meaningful interface tests
for new artifact types, malformed submissions, blocked tasks, and stale output
handling. Add a new renderer only if appropriate; arbitrary numerical tables can
already use the generic contract checker without a plot.
