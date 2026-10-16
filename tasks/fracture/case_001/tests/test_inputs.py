from pathlib import Path

import numpy as np

from benchcae_core.geometry.dxf import read_geometry
from benchcae_core.utils.io import sha256

TASK = Path(__file__).resolve().parents[1]


def test_original_cad_hashes_and_geometry():
    hashes = ["c6803601e874521f1138c653ea7beac348ebc2db829eba31ee36c2824b85bcd0",
              "5dd25f3f64a74d5ed7986a905cb6f1b8b73faba7095d89a7c4a9bc6cf300f0ad"]
    for i, digest in enumerate(hashes, 1):
        file = TASK / f"input/fracture_{i}.dxf"
        assert sha256(file) == digest
        g = read_geometry(file)
        assert g["dxf_version"] == "AC1012"
        assert g["insunits_code"] is None
        assert np.allclose(g["bounds_cad"], [[0, 0], [.065, .12]])
        assert g["entity_counts"] == {"SPLINE": 15, "LWPOLYLINE": 11 if i == 1 else 1}
        # Verify rational spline sampling against the known circular CAD boundary.
        xy = np.array(g["curves"][0]["points"])
        radii = np.linalg.norm(xy - [.02, .02], axis=1)
        assert np.max(abs(radii - .005)) < 2e-6
