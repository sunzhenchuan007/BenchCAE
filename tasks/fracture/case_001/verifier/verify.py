"""Evaluator-owned extension point. No scientific metric has been chosen."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--problem", required=True)
    parser.add_argument("--submission", required=True)
    parser.add_argument("--gt")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    report = {"status": "not_configured", "score": None, "physics_validated": False,
              "reason": "Case-specific metric and Ground Truth are not supplied. No scientific scoring performed."}
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
