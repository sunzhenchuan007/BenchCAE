"""Interface regressions; these tests make no scientific validity claims."""
from pathlib import Path
import shutil

import pytest
import yaml

from benchcae_core.cli import main
from benchcae_core.config import blockers, load_problem
from benchcae_core.geometry.dxf import read_geometry
from benchcae_core.runner.execution import prepare, run
from benchcae_core.scoring.contracts import check_artifacts
from benchcae_core.utils.io import ContractError, read_json, sha256, write_json

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "examples/smoke_task/problem.yaml"
REAL = ROOT / "tasks/fracture/case_001/problem.yaml"


@pytest.fixture(scope="module")
def completed(tmp_path_factory):
    path = tmp_path_factory.mktemp("completed") / "run"
    assert main(["smoke", "--out", str(path)]) == 0
    return path


@pytest.fixture
def submission(tmp_path, completed):
    target = tmp_path / "submission"
    shutil.copytree(completed / "output", target)
    return target


def test_end_to_end_is_explicitly_not_a_simulation(completed):
    run_info = read_json(completed / "run.json")
    report = read_json(completed / "contract_report.json")
    assert run_info["status"] == "completed"
    assert run_info["isolated"] is False
    assert report["data_kind"] == "synthetic"
    assert report["score"] is None
    assert report["physics_validated"] is False
    assert report["outputs"]["reaction_curve"]["rows"] == 21
    assert report["outputs"]["crack_path"]["rows"] == 13


def test_real_execution_blocked_before_start(tmp_path):
    assert len(blockers(load_problem(REAL))) == 12
    with pytest.raises(ContractError, match="Real case is blocked"):
        run(REAL, ROOT / "examples/smoke_submission", tmp_path / "run", "local-trusted", "generate.py")
    assert not (tmp_path / "run").exists()


def test_public_bundle_is_an_allowlist(tmp_path):
    result = prepare(REAL, tmp_path / "bundle")
    assert set(result["files"]) == {"instruction.md", "output_contract.md", "problem.yaml",
                                     "input/fracture_1.dxf", "input/fracture_2.dxf"}
    assert not (tmp_path / "bundle/verifier").exists()
    assert sha256(tmp_path / "bundle/input/fracture_1.dxf") == sha256(REAL.parent / "input/fracture_1.dxf")


def test_reused_run_refused(completed):
    with pytest.raises(ContractError, match="already exists"):
        run(SMOKE, ROOT / "examples/smoke_submission", completed, "local-trusted", "generate.py")


@pytest.mark.parametrize("bad", ["nan", "inf", "-inf", "not-a-number"])
def test_bad_numeric_cells_fail(submission, bad):
    file = submission / "reaction_curve.csv"
    text = file.read_text().splitlines()
    cells = text[1].split(",")
    cells[-1] = bad
    text[1] = ",".join(cells)
    file.write_text("\n".join(text) + "\n")
    assert check_artifacts(load_problem(SMOKE), submission)["status"] == "invalid_artifacts"


@pytest.mark.parametrize("filename", ["reaction_curve.csv", "crack_path.csv", "metadata.json", "crack_path.png"])
def test_missing_files_fail(submission, filename):
    (submission / filename).unlink()
    assert check_artifacts(load_problem(SMOKE), submission)["status"] == "invalid_artifacts"


def test_empty_csv_and_wrong_header_fail(submission):
    f = submission / "crack_path.csv"
    f.write_text("path_id,kind,point_index,step,x,y\n")
    assert check_artifacts(load_problem(SMOKE), submission)["status"] == "invalid_artifacts"
    f.write_text("x,y\n0,1\n")
    assert check_artifacts(load_problem(SMOKE), submission)["status"] == "invalid_artifacts"


def test_synthetic_cannot_be_relabelled_real(submission):
    m = read_json(submission / "metadata.json")
    m["data_kind"] = "real"
    write_json(submission / "metadata.json", m)
    assert check_artifacts(load_problem(SMOKE), submission)["status"] == "invalid_artifacts"


def test_invalid_png_fails(submission):
    (submission / "crack_path.png").write_bytes(b"not a PNG")
    assert check_artifacts(load_problem(SMOKE), submission)["status"] == "invalid_artifacts"


def test_report_deterministic(submission, tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    check_artifacts(load_problem(SMOKE), submission, a)
    check_artifacts(load_problem(SMOKE), submission, b)
    assert a.read_bytes() == b.read_bytes()


def test_different_task_can_declare_one_unplotted_table(tmp_path):
    p = {"id": "thermal/example", "data_kind": "synthetic",
         "outputs": [{"id": "temperature", "type": "temperature_field", "csv": "temperature.csv",
                      "columns": ["x", "temperature"], "numeric_columns": ["x", "temperature"]}]}
    (tmp_path / "temperature.csv").write_text("x,temperature\n0,300\n1,310\n")
    write_json(tmp_path / "metadata.json", {"schema_version": 1, "case_id": p["id"], "data_kind": "synthetic",
                                            "units": {"temperature": "K"}, "coordinate_frame": {"name": "local"}})
    report = check_artifacts(p, tmp_path)
    assert report["status"] == "valid_artifacts"
    assert set(report["outputs"]) == {"temperature"}
    assert report["score"] is None


def test_case_specific_verifier_is_not_implemented(tmp_path):
    report = tmp_path / "unconfigured.json"
    assert main(["verify", "--problem", str(REAL), "--submission", str(tmp_path), "--report", str(report)]) == 2
    assert read_json(report)["status"] == "not_configured"
    assert read_json(report)["score"] is None


def test_custom_trusted_task_verifier_dispatch(tmp_path):
    p = load_problem(SMOKE)
    p["verifier"] = {"status": "ready", "entry": "verifier.py"}
    problem = tmp_path / "problem.yaml"
    problem.write_text(yaml.safe_dump(p))
    # Fixture verifier checks plumbing only; deliberately does not assign a score.
    (tmp_path / "verifier.py").write_text(
        "import sys,json,pathlib\n"
        "pathlib.Path(sys.argv[sys.argv.index('--report')+1]).write_text(json.dumps({'status':'custom_fixture','score':None}))\n")
    report = tmp_path / "custom.json"
    assert main(["verify", "--problem", str(problem), "--submission", str(tmp_path), "--report", str(report)]) == 0
    assert read_json(report)["status"] == "custom_fixture"


@pytest.mark.parametrize("code,status", [("raise SystemExit(3)", "failed"), ("import time; time.sleep(20)", "timeout")])
def test_failed_and_timed_out_entries(tmp_path, code, status):
    p = load_problem(SMOKE)
    p["runner"]["timeout_seconds"] = .5
    task = tmp_path / "task"
    shutil.copytree(SMOKE.parent, task)
    (task / "problem.yaml").write_text(yaml.safe_dump(p))
    source = tmp_path / "source"
    source.mkdir()
    (source / "solver.py").write_text(code)
    manifest = run(task / "problem.yaml", source, tmp_path / "run", "local-trusted")
    assert manifest["status"] == status
    assert list((tmp_path / "run/output").iterdir()) == []


def test_escaped_output_rejected(tmp_path):
    p = load_problem(SMOKE)
    p["outputs"][0]["csv"] = "../outside.csv"
    f = tmp_path / "problem.yaml"
    f.write_text(yaml.safe_dump(p))
    with pytest.raises(ContractError, match="contained"):
        load_problem(f)


def test_step_is_explicitly_unsupported(tmp_path):
    with pytest.raises(ContractError, match="STEP adapter is not implemented"):
        read_geometry(tmp_path / "part.step")
