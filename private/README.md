# Evaluator-only data

There is no real Ground Truth in this repository. All contents below
`private/ground_truth/` except `.gitkeep` are ignored by Git. Never force-add
private data. For adversarial evaluation, store GT outside the agent host or
mount namespace as well: `.gitignore` is not an access-control mechanism.

After approval and convergence studies, place each GT's numerical artifacts,
metadata and provenance in an evaluator-controlled directory. Point the
verifier to it with `--gt`. The runner has no GT argument or mount.
