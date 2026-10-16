"""Fresh-run execution. Local backend is explicitly for trusted development code."""
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import uuid

from ..config import load_problem, require_runnable
from ..utils.io import ContractError, safe_file, sha256, write_json


def copy_plain_tree(source, destination):
    source, destination = Path(source), Path(destination)
    if source.is_symlink() or any(p.is_symlink() for p in source.rglob("*")):
        raise ContractError("Symlinks are not allowed in input/source trees")
    shutil.copytree(source, destination)


def prepare(problem_file, destination):
    """Allowlist the public bundle; never copy task/verifier, tests, or GT."""
    problem_file, destination = Path(problem_file).resolve(), Path(destination).resolve()
    problem = load_problem(problem_file)
    if destination.is_relative_to(problem_file.parent / "input"):
        raise ContractError("Public bundle must not be created inside its own inputs")
    if destination.exists():
        raise ContractError("Public bundle destination must not exist")
    destination.mkdir(parents=True)
    shutil.copy2(problem_file, destination / "problem.yaml")
    for name in ["instruction.md", "output_contract.md"]:
        file = safe_file(problem_file.parent, name)
        shutil.copy2(file, destination / name)
    inputs = problem_file.parent / "input"
    if inputs.is_dir():
        copy_plain_tree(inputs, destination / "input")
    return {"case_id": problem["id"], "bundle": str(destination),
            "files": sorted(p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file())}


def _stop(process):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait()


def run(problem_file, source, run_dir, backend="docker", entry="solver.py"):
    problem_file, source, run_dir = Path(problem_file).resolve(), Path(source).resolve(), Path(run_dir).resolve()
    p = load_problem(problem_file)
    require_runnable(p)
    if backend not in {"docker", "local-trusted"}:
        raise ContractError("Unknown execution backend")
    if run_dir.exists():
        raise ContractError("Run directory already exists; choose a fresh path to prevent stale artifacts")
    if run_dir.is_relative_to(source):
        raise ContractError("Run directory must not be inside submission source")
    safe_file(source, entry)
    if backend == "docker" and shutil.which("docker") is None:
        raise ContractError("Docker unavailable. local-trusted is only for your own development code")
    run_dir.mkdir(parents=True)
    prepare(problem_file, run_dir / "task")
    copy_plain_tree(source, run_dir / "source")
    output = run_dir / "output"
    output.mkdir()
    output.chmod(0o777)
    cfg = p["runner"]
    container_name = "benchcae-" + uuid.uuid4().hex
    if backend == "docker":
        command = ["docker", "run", "--rm", "--name", container_name,
                   "--network=none", "--read-only", "--cap-drop=ALL",
                   "--security-opt=no-new-privileges", "--pids-limit=128",
                   "--cpus", str(cfg["cpus"]), "--memory", cfg["memory"],
                   "--user", "65532:65532", "--tmpfs", "/tmp:rw,nosuid,size=256m",
                   "--mount", f"type=bind,src={run_dir / 'task'},dst=/task,readonly",
                   "--mount", f"type=bind,src={run_dir / 'source'},dst=/source,readonly",
                   "--mount", f"type=bind,src={output},dst=/output",
                   cfg["image"], "python", "/source/" + Path(entry).as_posix(),
                   "--problem", "/task/problem.yaml", "--output", "/output"]
    else:
        command = [sys.executable, str(run_dir / "source" / entry),
                   "--problem", str(run_dir / "task" / "problem.yaml"), "--output", str(output)]
    hashes = {f.relative_to(run_dir).as_posix(): sha256(f)
              for d in ["task", "source"] for f in (run_dir / d).rglob("*") if f.is_file()}
    env = {k: os.environ[k] for k in ["PATH", "SystemRoot", "WINDIR", "TEMP", "TMP", "DOCKER_HOST", "DOCKER_CONTEXT"] if k in os.environ}
    env.update(PYTHONHASHSEED="0", PYTHONUTF8="1", PYTHONNOUSERSITE="1",
               OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MPLCONFIGDIR=str(run_dir / "mpl-cache"))
    status, code = "failed", None
    try:
        with (run_dir / "execution.log").open("wb") as log:
            process = subprocess.Popen(command, cwd=run_dir, env=env, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=os.name != "nt")
            try:
                code = process.wait(timeout=cfg["timeout_seconds"])
                status = "completed" if code == 0 else "failed"
            except subprocess.TimeoutExpired:
                _stop(process)
                status = "timeout"
    finally:
        if backend == "docker":
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, check=False)
        manifest = {"schema_version": 1, "case_id": p["id"], "data_kind": p["data_kind"],
                    "status": status, "returncode": code, "backend": backend,
                    "isolated": backend == "docker", "command": command,
                    "timeout_seconds": cfg["timeout_seconds"], "input_sha256": hashes,
                    "physics_validated": False, "output": str(output)}
        write_json(run_dir / "run.json", manifest)
    return manifest
