import logging

import numpy as np
from pykarstnsim.models import Surface

from pykarstnsim_demo.models.vk import VkProjectBox

LOGGER = logging.getLogger(__name__)


def load_water_tables(
    voxels: np.ndarray, project_box: VkProjectBox
) -> dict[int, Surface]:
    """Build a triangulated water-table surface for each groundwater body present in the voxels."""

    if voxels.ndim != 4 or voxels.shape[-1] < 2:
        raise ValueError(
            "Voxels array must have shape (nx, ny, nz, 2) including gwb identifiers"
        )

    nx, ny, nz, _ = voxels.shape
    if nz == 0:
        return {}

    dx = project_box.width / max(nx - 1, 1) if nx > 1 else 0.0
    dy = project_box.height / max(ny - 1, 1) if ny > 1 else 0.0
    dz = project_box.depth / nz

    gwb_ids = voxels[:, :, :, 1]
    unique_gwb_ids: list[int] = np.unique(gwb_ids).flatten().tolist()
    LOGGER.debug(f"Unique GWB IDs in voxel data: {unique_gwb_ids}")

    surfaces: dict[int, Surface] = {}

    for gwb_id in unique_gwb_ids:
        if gwb_id <= 0:
            continue

        # highest occupied z-layer for each (x, y) column within this groundwater body
        top_layer = np.full((nx, ny), -1, dtype=np.int32)
        gwb_mask = gwb_ids == gwb_id

        for ix in range(nx):
            column = gwb_mask[ix]
            for iy in range(ny):
                hits = np.flatnonzero(column[iy])
                if hits.size > 0:
                    top_layer[ix, iy] = int(hits[-1])

        valid_mask = top_layer >= 0
        if not valid_mask.any():
            continue

        xs, ys = np.where(valid_mask)
        x_min, x_max = int(xs.min()), int(xs.max())
        y_min, y_max = int(ys.min()), int(ys.max())

        width = x_max - x_min + 1
        height = y_max - y_min + 1

        vertex_indices = -np.ones((height, width), dtype=np.int32)
        vertices: list[list[float]] = []

        for local_y, global_y in enumerate(range(y_min, y_max + 1)):
            y_coord = global_y * dy
            for local_x, global_x in enumerate(range(x_min, x_max + 1)):
                top_idx = top_layer[global_x, global_y]
                if top_idx < 0:
                    continue
                x_coord = global_x * dx
                z_coord = (top_idx + 1) * dz + project_box.min_elevation
                vertex_indices[local_y, local_x] = len(vertices)
                vertices.append([x_coord, y_coord, z_coord])

        triangles: list[list[int]] = []
        for local_y in range(height - 1):
            for local_x in range(width - 1):
                v1 = vertex_indices[local_y, local_x]
                v2 = vertex_indices[local_y, local_x + 1]
                v3 = vertex_indices[local_y + 1, local_x]
                v4 = vertex_indices[local_y + 1, local_x + 1]
                if min(v1, v2, v3, v4) < 0:
                    continue
                triangles.append([v1, v2, v3])
                triangles.append([v2, v4, v3])

        if not triangles:
            LOGGER.warning(
                "Skipping groundwater body %s because no triangles could be generated.",
                gwb_id,
            )
            continue

        surfaces[gwb_id] = Surface.from_vertices_and_triangles(
            np.asarray(vertices, dtype=np.float64),
            np.asarray(triangles, dtype=np.int32),
        )
        LOGGER.info(
            "Built water table surface for GWB %s with %d vertices and %d triangles.",
            gwb_id,
            len(vertices),
            len(triangles),
        )

    return surfaces
