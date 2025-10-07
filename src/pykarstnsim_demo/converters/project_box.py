import logging
from typing import Literal

import numpy as np
from pykarstnsim.models import ProjectBox

from pykarstnsim_demo.models.shared import PERMEABILITY_MAP, Permeability, Point3DInt
from pykarstnsim_demo.models.vk import VkGeologicalUnit, VkProjectBox, VkStratigraphy

LOGGER = logging.getLogger(__name__)

SKY = VkGeologicalUnit(
    name="Sky", permeability=Permeability.NonKarstified, strati_unit_id=0
)
DUMMY = VkGeologicalUnit(
    name="Dummy", permeability=Permeability.Undefined, strati_unit_id=0
)


def load_project_box(
    box: VkProjectBox,
    stratigraphy: VkStratigraphy,
    compute_resolution: Point3DInt,
    voxels: np.ndarray,
    voxels_units: list[int],
    r_min_pervious: Literal["auto"] | float = "auto",
    r_min_impervious: Literal["auto"] | float = "auto",
) -> ProjectBox:

    units = stratigraphy.root

    # move to local box coordinates
    basis = (0, 0, box.min_elevation)
    u = (box.width, 0.0, 0.0)
    v = (0.0, box.height, 0.0)
    w = (0.0, 0.0, box.depth)
    cells_u = compute_resolution.x
    cells_v = compute_resolution.y
    cells_w = compute_resolution.z

    # we will find the "top" altitude of each gwb cell
    gwbs = [0] * (cells_u * cells_v)

    NO_VALUE = -99999.0

    unique_ranks = voxels[:, :, :, 0].flatten()
    unique_ranks = np.unique(unique_ranks).tolist()
    LOGGER.debug(f"Unique ranks in voxel data: {unique_ranks}")

    rank_count = len(units)

    # TODO make it work for not base projects
    is_base = False

    rank_to_unit: dict[int, VkGeologicalUnit] = {}

    j = 0
    for unit_id in voxels_units:
        unit = next(filter(lambda uN: uN.strati_unit_id == unit_id, units), None)
        if unit:
            id = rank_count - j if is_base else j + 1
            rank_to_unit[id] = unit
        else:
            LOGGER.warning(f"No geological unit found with strati_unit_id={unit_id}")
        j += 1

    # if the counts do not mach, there must be a dummy, so add it
    if len(voxels_units) < rank_count:
        id = 1 if is_base else rank_count
        rank_to_unit[id] = DUMMY

    # add the Sky, always rank 0
    rank_to_unit[0] = SKY

    for rank in unique_ranks:
        unit = rank_to_unit[rank]
        LOGGER.info(f"Rank {rank}: {unit.name} (permeability={unit.permeability})")

    densities = [NO_VALUE] * (cells_u * cells_v * cells_w)
    karstification_potential = [NO_VALUE] * (cells_u * cells_v * cells_w)

    if r_min_pervious == "auto":
        base_density = cells_w / w[2]
    else:
        base_density = r_min_pervious
    if r_min_impervious == "auto":
        sparse_density = base_density * 2
    else:
        sparse_density = r_min_impervious

    if base_density > 1 or sparse_density > 1:
        raise ValueError(
            f"Density modifier too high, resulting density > 1 (base={base_density}, sparse={sparse_density})"
        )

    # for each cell of the compute resolution, get the corresponding rank from the voxels
    nx, ny, nz, _ = voxels.shape
    for iu in range(cells_u):
        for iv in range(cells_v):
            for iw in range(cells_w):
                index = iu + cells_u * (iv + cells_v * iw)
                # map (iu, iv, iw) in [0, cells_u/v/w] to (ix, iy, iz) in [0, nx/ny/nz]
                ix = min(int(iu / cells_u * nx), nx - 1)
                iy = min(int(iv / cells_v * ny), ny - 1)
                iz = min(int(iw / cells_w * nz), nz - 1)
                rank = voxels[ix, iy, iz, 0]
                gwb_id = voxels[ix, iy, iz, 1]
                if gwb_id > 0:
                    # in a gwb, set potential to 1.0 (will normalize later)
                    potential = 1.0
                    gwbs[iv * cells_w + iw] = max(gwbs[iv * cells_w + iw], gwb_id)
                elif rank > 0:
                    unit = rank_to_unit[rank]
                    potential = PERMEABILITY_MAP.get(unit.permeability, NO_VALUE)
                    if potential == NO_VALUE:
                        LOGGER.warning(
                            f"Unknown permeability '{unit.permeability}' for unit {unit.name}"
                        )
                else:
                    # ignore sky
                    continue

                karstification_potential[index] = potential
                if potential < 0:
                    # density is already NO_VALUE
                    continue
                densities[index] = base_density if potential > 0 else sparse_density

    project_box = ProjectBox(
        basis, u, v, w, cells_u, cells_v, cells_w, densities, karstification_potential
    )

    return project_box
