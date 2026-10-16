import hashlib
import json
from pathlib import Path

import yaml


class ContractError(ValueError):
    """Invalid configuration or submission, never an implicit passing result."""


def read_yaml(path):
    with Path(path).open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_json(path):
    def invalid(value):
        raise ContractError(f"Non-finite JSON value: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=invalid)


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_file(root, relative):
    root = Path(root).resolve()
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ContractError(f"Unsafe artifact path: {relative}")
    path = root / rel
    if any(p.is_symlink() for p in [path, *path.parents] if p != root.parent):
        raise ContractError(f"Symlink not allowed: {relative}")
    if not path.resolve().is_relative_to(root) or not path.is_file():
        raise ContractError(f"Missing or escaped artifact: {relative}")
    return path
