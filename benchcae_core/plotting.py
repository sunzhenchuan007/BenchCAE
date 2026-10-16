"""Render declared output types. Plots are presentation artifacts, never evidence of a solve."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .geometry.dxf import read_geometry
from .scoring.contracts import csv_table
from .utils.io import ContractError, read_json, safe_file


def plot_outputs(problem, problem_dir, submission):
    submission = Path(submission)
    meta = read_json(safe_file(submission, "metadata.json"))
    synthetic = problem["data_kind"] == "synthetic"
    label = "SYNTHETIC INTERFACE TEST — NOT A SIMULATION" if synthetic else "Submitted numerical data — unverified"
    outputs = []
    for spec in problem["outputs"]:
        if "png" not in spec:
            continue
        rows = csv_table(submission, spec)
        fig, ax = plt.subplots(figsize=(7, 5))
        if spec["type"] == "reaction_curve":
            x = [float(r["displacement"]) for r in rows]
            y = [float(r["reaction"]) for r in rows]
            ax.plot(x, y, color="#186b9b", marker=".", ms=3)
            ax.set(xlabel=f"Displacement [{meta['units']['displacement']}]",
                   ylabel=f"Reaction [{meta['units']['reaction']}]", title="Reaction–displacement")
        elif spec["type"] == "crack_path":
            # Only an explicitly declared native CAD frame can be overlaid by this MVP renderer.
            if meta["coordinate_frame"].get("name") != "original_cad_xy":
                plt.close(fig)
                raise ContractError("Renderer requires original_cad_xy; convert other frames in your task-specific postprocessor")
            geometry = safe_file(problem_dir, problem["geometry"]["primary"])
            for c in read_geometry(geometry)["curves"]:
                xy = np.asarray(c["points"])
                ax.plot(xy[:, 0], xy[:, 1], color="#89949d", lw=.9)
            keys = sorted({(r["path_id"], r["kind"]) for r in rows})
            for path_id, kind in keys:
                subset = [r for r in rows if r["path_id"] == path_id and r["kind"] == kind]
                if kind not in {"initial", "propagated"}:
                    raise ContractError("Unknown crack kind")
                ax.plot([float(r["x"]) for r in subset], [float(r["y"]) for r in subset],
                        "--" if kind == "initial" else "-", lw=2,
                        color="#2470a0" if kind == "initial" else "#d24b38", label=f"{path_id}: {kind}")
            ax.set_aspect("equal")
            ax.set(xlabel=f"CAD x [{meta['units']['length']}]", ylabel=f"CAD y [{meta['units']['length']}]", title="Crack path on original CAD")
            ax.legend(fontsize=8)
        else:
            plt.close(fig)
            raise ContractError(f"No renderer for {spec['type']}; add a task-specific renderer")
        ax.grid(alpha=.2)
        fig.text(.5, .015, label, ha="center", fontsize=8, color="#a33c30")
        fig.tight_layout(rect=(0, .04, 1, 1))
        target = submission / spec["png"]
        if Path(spec["png"]).is_absolute() or ".." in Path(spec["png"]).parts or target.is_symlink():
            raise ContractError("Unsafe plot path")
        if not target.resolve().is_relative_to(submission.resolve()):
            raise ContractError("Escaped plot path")
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=150)
        plt.close(fig)
        outputs.append(str(target))
    return outputs
