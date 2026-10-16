"""DXF inspection and tessellation, not a FEM mesh or boundary-condition inference."""
from collections import Counter
from pathlib import Path

import ezdxf
import numpy as np
from ezdxf import path as dxfpath

from ..utils.io import ContractError, sha256, write_json


def read_geometry(filename, tolerance=1e-6):
    filename = Path(filename)
    if filename.suffix.lower() != ".dxf":
        raise ContractError("MVP supports DXF only; STEP adapter is not implemented")
    doc = ezdxf.readfile(filename)
    curves = []
    for entity in doc.modelspace():
        try:
            points = np.array([tuple(v) for v in dxfpath.make_path(entity).flattening(tolerance)])
        except (TypeError, ValueError, NotImplementedError) as exc:
            raise ContractError(f"Unsupported DXF entity {entity.dxftype()}") from exc
        if points.ndim != 2 or len(points) < 2 or not np.isfinite(points).all():
            raise ContractError("Invalid DXF path")
        if not np.allclose(points[:, 2], 0, atol=tolerance, rtol=0):
            raise ContractError("Only planar XY DXF is supported")
        curves.append({"handle": entity.dxf.handle, "type": entity.dxftype(),
                       "layer": entity.dxf.layer, "points": points[:, :2].tolist()})
    if not curves:
        raise ContractError("Empty DXF")
    all_points = np.concatenate([c["points"] for c in curves])
    units_present = "$INSUNITS" in doc.header
    return {"file": filename.name, "sha256": sha256(filename), "dxf_version": doc.loaded_dxfversion,
            "reader_internal_dxf_version": doc.dxfversion,
            "insunits_code": int(doc.header.get("$INSUNITS", 0)) if units_present else None,
            "unit_confirmed": False,
            "entity_counts": dict(Counter(e.dxftype() for e in doc.modelspace())),
            "bounds_cad": [all_points.min(axis=0).tolist(), all_points.max(axis=0).tolist()],
            "flattening_tolerance_cad": tolerance, "curves": curves}


def inspect_geometry(inputs, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    reports = []
    fig, axes = plt.subplots(1, len(inputs), figsize=(5 * len(inputs), 7), squeeze=False)
    for ax, filename in zip(axes[0], inputs):
        data = read_geometry(filename)
        for c in data["curves"]:
            xy = np.asarray(c["points"])
            ax.plot(xy[:, 0], xy[:, 1], color="#243f55", lw=1)
        ax.set(title=Path(filename).stem, xlabel="CAD x (unit unconfirmed)", ylabel="CAD y (unit unconfirmed)")
        ax.set_aspect("equal")
        ax.grid(alpha=.2)
        write_json(out / (Path(filename).stem + ".json"), data)
        reports.append({k: v for k, v in data.items() if k != "curves"})
    fig.suptitle("Original CAD geometry — no physics inferred")
    fig.tight_layout()
    fig.savefig(out / "geometry.png", dpi=170)
    plt.close(fig)
    write_json(out / "inspection.json", reports)
    return reports
