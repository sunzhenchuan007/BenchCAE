"""Generic artifact checks only. Scientific metrics belong to each task."""
import csv
import math
from pathlib import Path

from PIL import Image

from ..utils.io import ContractError, read_json, safe_file, sha256, write_json

MAX_BYTES = 20_000_000
MAX_ROWS = 100_000


def csv_table(root, output):
    file = safe_file(root, output["csv"])
    if file.stat().st_size > MAX_BYTES:
        raise ContractError("CSV exceeds 20 MB")
    with file.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != output["columns"]:
            raise ContractError(f"{output['csv']}: expected header {output['columns']}")
        rows = []
        for row in reader:
            if len(rows) >= MAX_ROWS:
                raise ContractError("CSV exceeds row limit")
            if None in row or any(v is None or not v.strip() for v in row.values()):
                raise ContractError("Missing/extra CSV cells")
            for key in output.get("numeric_columns", []):
                try:
                    value = float(row[key])
                except (TypeError, ValueError) as exc:
                    raise ContractError(f"{key}: expected a numeric value") from exc
                if not math.isfinite(value):
                    raise ContractError("NaN/Inf is forbidden")
            rows.append(row)
    if not rows:
        raise ContractError("Empty CSV")
    return rows


def check_artifacts(problem, submission, report=None):
    result = {"case_id": problem["id"], "data_kind": problem["data_kind"],
              "scope": "artifact_contract_only", "score": None,
              "physics_validated": False, "metrics_status": "not_configured"}
    try:
        meta_file = safe_file(submission, "metadata.json")
        if meta_file.stat().st_size > MAX_BYTES:
            raise ContractError("Metadata exceeds byte limit")
        meta = read_json(meta_file)
        if meta.get("schema_version") != 1 or meta.get("case_id") != problem["id"]:
            raise ContractError("Metadata schema/case ID mismatch")
        if meta.get("data_kind") != problem["data_kind"]:
            raise ContractError("Synthetic/real mismatch")
        if not isinstance(meta.get("units"), dict) or not meta["units"] or not all(isinstance(u, str) and u.strip() for u in meta["units"].values()):
            raise ContractError("Units must be explicitly declared")
        if not isinstance(meta.get("coordinate_frame"), dict) or not meta["coordinate_frame"]:
            raise ContractError("Coordinate frame must be explicitly declared")
        checked = {}
        for output in problem["outputs"]:
            entry = {}
            if "csv" in output:
                rows = csv_table(submission, output)
                entry.update(rows=len(rows), csv_sha256=sha256(safe_file(submission, output["csv"])))
            if "png" in output:
                file = safe_file(submission, output["png"])
                if file.stat().st_size > MAX_BYTES:
                    raise ContractError("PNG exceeds byte limit")
                with Image.open(file) as im:
                    if im.format != "PNG" or im.width * im.height > 20_000_000:
                        raise ContractError("Invalid PNG")
                    im.verify()
                entry["png_sha256"] = sha256(file)
            checked[output["id"]] = entry
        result.update(status="valid_artifacts", outputs=checked)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result.update(status="invalid_artifacts", reasons=[str(exc)])
    if report:
        write_json(report, result)
    return result
