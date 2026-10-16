from pathlib import Path

from .utils.io import ContractError, read_yaml


def field_value(problem, dotted_path):
    value = problem
    for key in dotted_path.split("."):
        value = value.get(key) if isinstance(value, dict) else None
    return value


def load_problem(path):
    path = Path(path)
    p = read_yaml(path)
    if not isinstance(p, dict) or p.get("schema_version") != 1:
        raise ContractError("Unsupported problem schema")
    if not p.get("outputs") or len({o["id"] for o in p["outputs"]}) != len(p["outputs"]):
        raise ContractError("Outputs must be declared with unique IDs")
    filenames = []
    for output in p["outputs"]:
        if not any(k in output for k in ("csv", "png")):
            raise ContractError("Each output needs a CSV or PNG artifact")
        for kind in ("csv", "png"):
            if kind in output:
                rel = Path(output[kind])
                if rel.is_absolute() or ".." in rel.parts:
                    raise ContractError("Output paths must be relative and contained")
                filenames.append(output[kind])
        if "csv" in output:
            columns = output.get("columns", [])
            if not columns or len(set(columns)) != len(columns):
                raise ContractError("CSV columns must be nonempty and unique")
            if not set(output.get("numeric_columns", [])).issubset(columns):
                raise ContractError("Numeric columns must belong to the CSV header")
    if len(filenames) != len(set(filenames)):
        raise ContractError("Output filenames must be unique")
    if p.get("data_kind") not in {"real", "synthetic"}:
        raise ContractError("data_kind must be real or synthetic")
    return p


def blockers(p):
    if p["data_kind"] == "synthetic":
        return [] if p.get("status") == "synthetic_only" else ["synthetic status"]
    missing = [k for k in p.get("required_fields", []) if field_value(p, k) is None]
    if p.get("status") != "ready":
        missing.append("status is not ready")
    return missing


def require_runnable(p):
    missing = blockers(p)
    if missing:
        raise ContractError("Real case is blocked: " + ", ".join(missing))
