# Architecture sources inspected

Read from the official GitHub repositories on 2026-10-16, pinned to the commits
below. No implementation code was copied.

| Project | Commit | Files inspected / design used |
|---|---|---|
| [BenchCAD](https://github.com/BenchCAD-org/benchcad-2-main/tree/6d29a877e9c98e1c19e1172427edaba96d8fd338) | `6d29a877e9c98e1c19e1172427edaba96d8fd338` | `docs/RUNNING.md`, `pyproject.toml`, `envs/tasks.py`, T1 `task.toml`, common score dispatch; unified entry, declarative tasks and artifact-based evaluation |
| [Terminal-Bench-Science](https://github.com/harbor-framework/terminal-bench-science/tree/01b3c488061353987d6407b170c2ffbc851802f2) | `01b3c488061353987d6407b170c2ffbc851802f2` | README, CONTRIBUTING and baseline-free-localization's task/environment/tests files; public instruction/environment separate from evaluator inputs and tests |

The inspected TB-Science task is under
`tasks/engineering-sciences/mechanical-engineering/baseline-free-localization/`.
Its task.toml declares submitted artifacts and `environment_mode = "separate"`;
agent and verifier have distinct Dockerfiles, and tests emit a numeric reward.
Its real experimental data/algorithms are unrelated to this fracture case and
were not imported. BenchCAD's run documentation explicitly distinguishes a
Docker sandbox from local development subprocess execution and checks sample
oracle submissions. BenchCAE adopts the separation and explicit interfaces,
without inheriting their task-specific metrics or full agent harness.

The current prototype is not a Harbor task-format compatibility implementation.
There is no requirement that all BenchCAE cases share a scientific metric.
