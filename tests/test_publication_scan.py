"""Use assembled dummy strings so test fixtures do not resemble live secrets."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("publication_scan", Path(__file__).resolve().parents[1] / "tools/check_public_files.py")
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


@pytest.mark.parametrize("value,category", [
    ("Z" + ":/" + "Users" + "/example/project", "windows_absolute_path"),
    ("sk-" + "a" * 40, "api_token"),
    ("-----BEGIN " + "PRIVATE KEY-----", "private_key"),
    ("example" + "@" + "example.invalid", "email_address"),
    (":".join(["aa"] * 6), "mac_address"),
])
def test_flags_sensitive_shapes_without_echoing_values(value, category):
    result = scanner.scan_text("sample.txt", value)
    assert any(r["category"] == category for r in result)
    assert all(value not in str(r) for r in result)


def test_relative_paths_and_public_links_are_allowed():
    assert scanner.scan_text("README.md", "tasks/fracture/case_001/input https://github.com/example/project") == []
