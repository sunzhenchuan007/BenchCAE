# Publication hygiene

Only project source, documentation, declared public task inputs and tests belong
in this repository. Login data, local agent settings, machine identifiers,
personal filesystem paths, runtime logs, results and real GT do not.

Before committing, inspect the actual Git index:

```sh
python tools/check_public_files.py
git add <reviewed-project-paths>
python tools/check_public_files.py --staged
git diff --cached --stat
```

The scan reports filenames, line numbers and categories without echoing matched
values. It scans text, including ASCII DXF metadata. Binary candidates require
manual review. It does not read login stores or send files to an external
scanning service. Heuristics cannot recognize every possible secret, so review
new inputs and metadata as well. Never bypass ignored paths using `git add -f`.

Runtime reports can contain local absolute paths. Keep them under ignored
`results/`; do not publish run-directory archives or the virtual environment.
Git ignore rules are not access control and do not remove already-tracked files.

Use GitHub's public username and a GitHub noreply address for commit attribution
when personal contact information should remain private. Account authentication
stays in the existing GitHub credential provider, outside the repository.

The initial publication review removed a machine-specific absolute path from
the local-validation document. All public candidates, including the ASCII CAD
files, then passed the scan. Thirty interface/privacy tests passed locally.
Private data and generated runtime reports remain excluded. This records the
review scope, not a guarantee that heuristic scanning detects all secrets.
