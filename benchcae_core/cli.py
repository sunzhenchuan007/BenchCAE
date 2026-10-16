import argparse
import json
from pathlib import Path
import subprocess
import sys

from .config import blockers, load_problem
from .geometry.dxf import inspect_geometry
from .plotting import plot_outputs
from .runner.execution import prepare, run
from .scoring.contracts import check_artifacts
from .utils.io import ContractError, read_json, safe_file, write_json

DEFAULT_PROBLEM = "tasks/fracture/case_001/problem.yaml"


def main(argv=None):
    parser = argparse.ArgumentParser(description="BenchCAE task runner. Metrics are task-specific and currently unconfigured.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ["inspect", "check", "prepare", "run", "plot", "validate", "verify"]:
        cmd = commands.add_parser(name)
        cmd.add_argument("--problem", default=DEFAULT_PROBLEM)
        if name in {"inspect", "prepare"}:
            cmd.add_argument("--out", required=True)
        if name == "run":
            cmd.add_argument("--source", required=True)
            cmd.add_argument("--out", required=True)
            cmd.add_argument("--entry", default="solver.py")
            cmd.add_argument("--backend", choices=["docker", "local-trusted"], default="docker")
        if name in {"plot", "validate", "verify"}:
            cmd.add_argument("--submission", required=True)
        if name in {"validate", "verify"}:
            cmd.add_argument("--report", required=True)
        if name == "verify":
            cmd.add_argument("--gt")
    smoke = commands.add_parser("smoke", help="Run the synthetic interface fixture; no solver or scientific score")
    smoke.add_argument("--out", required=True)
    smoke.add_argument("--backend", choices=["local-trusted", "docker"], default="local-trusted")
    args = parser.parse_args(argv)
    try:
        if args.command == "smoke":
            root = Path(__file__).resolve().parents[1]
            problem_file = root / "examples/smoke_task/problem.yaml"
            manifest = run(problem_file, root / "examples/smoke_submission", args.out, args.backend, "generate.py")
            if manifest["status"] != "completed":
                result = manifest
                code = 1
            else:
                p = load_problem(problem_file)
                plot_outputs(p, problem_file.parent, manifest["output"])
                result = check_artifacts(p, manifest["output"], Path(args.out) / "contract_report.json")
                code = 0 if result["status"] == "valid_artifacts" else 1
        else:
            problem_file = Path(args.problem).resolve()
            p = load_problem(problem_file)
            code = 0
            if args.command == "check":
                missing = blockers(p)
                result = {"case_id": p["id"], "status": p["status"], "missing": missing,
                          "metric_status": p.get("verifier", {}).get("status", "not_configured")}
                code = 2 if missing else 0
            elif args.command == "inspect":
                paths = [safe_file(problem_file.parent, v["path"]) for v in p["geometry"]["variants"]]
                result = inspect_geometry(paths, args.out)
            elif args.command == "prepare":
                result = prepare(problem_file, args.out)
            elif args.command == "run":
                result = run(problem_file, args.source, args.out, args.backend, args.entry)
                code = 0 if result["status"] == "completed" else 1
            elif args.command == "plot":
                result = plot_outputs(p, problem_file.parent, args.submission)
            elif args.command == "validate":
                result = check_artifacts(p, args.submission, args.report)
                code = 0 if result["status"] == "valid_artifacts" else 1
            elif args.command == "verify":
                report = Path(args.report).resolve()
                if p.get("verifier", {}).get("status") != "ready":
                    result = {"status": "not_configured", "score": None, "physics_validated": False,
                              "reason": "Case-specific metric has not been selected; no scientific scoring performed."}
                    write_json(report, result)
                    code = 2
                else:
                    # Only evaluator-owned task code is executable here, never submission code.
                    entry = safe_file(problem_file.parent, p["verifier"]["entry"])
                    if report.exists():
                        raise ContractError("Verifier report already exists; choose a fresh path")
                    command = [sys.executable, str(entry), "--problem", str(problem_file),
                               "--submission", str(Path(args.submission).resolve()), "--report", str(report)]
                    if args.gt:
                        command += ["--gt", str(Path(args.gt).resolve())]
                    completed = subprocess.run(command, timeout=p["verifier"].get("timeout_seconds", 120), check=False)
                    code = completed.returncode
                    result = read_json(report) if report.is_file() else {"status": "verifier_failed", "score": None}
                    if not report.is_file():
                        code = 1
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return code
    except (ContractError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
