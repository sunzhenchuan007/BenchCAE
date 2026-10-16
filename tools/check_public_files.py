"""Heuristic publication scan; reports locations/categories, never matched secrets.

Scans Git-tracked and nonignored candidate files, or the exact Git index with
--staged. Does not inspect account stores or upload content to external services.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess


PATTERNS = {
    "windows_absolute_path": r"(?i)(?<![A-Za-z])[A-Z]:[\\/]",
    "home_directory_path": r"/(?:Users|home)/[^/\s]+",
    "network_share_path": r"\\\\[A-Za-z0-9_.-]+\\[A-Za-z0-9_$.-]+",
    "private_key": r"-----BEGIN (?:RSA |OPENSSH |EC |DSA |ENCRYPTED )?PRIVATE KEY-----",
    "api_token": r"(?:sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16})",
    "jwt": r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
    "credential_assignment": r'''(?i)["']?(?:access_token|refresh_token|id_token|api_key|client_secret|password)["']?\s*[:=]\s*["'][^"'\r\n]{8,}["']''',
    "uuid_identifier": r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    "mac_address": r"(?i)\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b",
    "email_address": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "windows_security_identifier": r"\bS-1-5-21-\d+-\d+-\d+(?:-\d+)?\b",
}
PRIVATE_PARTS = {".codex", ".agents", ".aws", ".ssh", ".venv", "__pycache__", ".pytest_cache", "tmp"}


def scan_text(name, text):
    findings = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for category, pattern in PATTERNS.items():
            if re.search(pattern, line):
                findings.append({"file": name, "line": lineno, "category": category})
    return findings


def scan(root, staged=False):
    root = Path(root)
    args = ["git", "-C", str(root), "ls-files", "--cached", "-z"]
    if not staged:
        args += ["--others", "--exclude-standard"]
    names = sorted(set(os.fsdecode(n) for n in subprocess.check_output(args).split(b"\0") if n))
    findings = [] if names else [{"category": "no_files_to_review"}]
    for name in names:
        p = Path(name)
        private = any(part in PRIVATE_PARTS for part in p.parts)
        private |= p.name.startswith(".env") or p.suffix.lower() in {".pem", ".key", ".p12", ".pfx", ".log", ".db", ".sqlite", ".sqlite3"}
        private |= p.name in {"auth.json", "credentials.json"} or p.name.startswith("credentials.")
        private |= p.parts[0] == "results" and name != "results/.gitkeep"
        private |= p.parts[0] == "private" and name not in {"private/README.md", "private/ground_truth/.gitkeep"}
        if private:
            findings.append({"file": name, "category": "private_file"})
            continue
        if (root / name).is_symlink():
            findings.append({"file": name, "category": "symlink"})
            continue
        if staged:
            content = subprocess.check_output(["git", "-C", str(root), "show", ":" + name])
        elif (root / name).is_file():
            content = (root / name).read_bytes()
        else:
            continue
        if b"\0" in content:
            findings.append({"file": name, "category": "binary_requires_manual_review"})
            continue
        findings.extend(scan_text(name, content.decode("utf-8", errors="replace")))
    return {"scope": "git_index" if staged else "public_candidates", "files_checked": len(names),
            "passed": not findings, "findings": findings,
            "limitation": "Heuristic scan; cannot prove absence of every possible secret or identifier."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    result = scan(Path(__file__).resolve().parents[1], args.staged)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
