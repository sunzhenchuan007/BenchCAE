"""Synthetic fixture generator, NOT a numerical solver or a reference solution."""
import argparse
import csv
import json
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--problem", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    problem = yaml.safe_load(Path(args.problem).read_text(encoding="utf-8"))
    if problem["data_kind"] != "synthetic":
        raise ValueError("Fixture generator refuses real cases")
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "reaction_curve.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["step", "segment", "displacement", "reaction"])
        for i in range(21):
            u = i / 20
            writer.writerow([i, 0, u, 2 * u if u <= .5 else 1.5 - u])
    with (out / "crack_path.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["path_id", "kind", "point_index", "step", "x", "y"])
        writer.writerows([["demo", "initial", 0, 0, 0, .065], ["demo", "initial", 1, 0, .01, .065]])
        for i in range(11):
            writer.writerow(["demo", "propagated", i, i + 1, .01 + .003 * i, .065 + .0008 * i])
    metadata = {"schema_version": 1, "case_id": problem["id"], "data_kind": "synthetic",
                "units": {"displacement": "arbitrary", "reaction": "arbitrary", "length": "unconfirmed CAD unit"},
                "coordinate_frame": {"name": "original_cad_xy"},
                "solver": {"status": "not_run", "description": "Synthetic interface fixture. No physical model or solve."}}
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
