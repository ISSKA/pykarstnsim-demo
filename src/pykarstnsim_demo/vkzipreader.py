import logging
from dataclasses import dataclass
from typing import Any
from zipfile import ZipFile

import numpy as np
from pydantic import BaseModel

from pykarstnsim_demo.models.io import SimulationParameters
from pykarstnsim_demo.models.shared import Point2D, Point3DInt
from pykarstnsim_demo.models.vk import (
    VkDemResolution,
    VkFault,
    VkGroundwaterBody,
    VkProjectBox,
    VkSpring,
    VkStratigraphy,
    VkVoxelsHeader,
    VkVoxelsUnits,
)

LOGGER = logging.getLogger(__name__)


@dataclass
class VkZipContent:
    simulation_params: SimulationParameters
    project_box: VkProjectBox
    dem_resolution: VkDemResolution
    surface_data: np.ndarray
    stratigraphy: VkStratigraphy
    compute_resolution: Point3DInt
    voxels_header: VkVoxelsHeader
    voxels: np.ndarray  # shape (nx, ny, nz, 2)
    voxels_units: VkVoxelsUnits
    faults: list[VkFault]
    springs: list[VkSpring]
    gwbs: list[VkGroundwaterBody]
    surface_resolution: Point2D
    resampled_dem_resolution: VkDemResolution


def load_voxels(voxels_lines: list[str]) -> tuple[VkVoxelsHeader, np.ndarray]:
    """Load voxel grid and return as ndarray of shape (nx, ny, nz, 2) where last dimension is (rank, gwb_id)"""
    # file has 3 lines:
    # format is:
    # XMIN=563987.601 XMAX=571512.301 YMIN=252987.602 YMAX=260512.302 ZMIN=0.0 ZMAX=1100.0 NUMBERX=200 NUMBERY=200 NUMBERZ=29 NOVALUE=0
    # rank gwb_id
    # ... ...
    if len(voxels_lines) < 3:
        raise ValueError("Voxel file must have at least 3 lines")

    # parse the header
    header = voxels_lines[0]
    header_parts = header.split()
    if len(header_parts) != 10:
        raise ValueError("Malformed voxel header line (expected 10 tokens)")
    xmin, xmax, ymin, ymax, zmin, zmax, nx, ny, nz, novalue = map(
        float, [part.split("=")[1] for part in header_parts]
    )
    nx, ny, nz, novalue = int(nx), int(ny), int(nz), int(novalue)
    # sanity check
    expected_n_voxels = nx * ny * nz
    actual_n_voxels = len(voxels_lines) - 2
    if expected_n_voxels != actual_n_voxels:
        raise ValueError(
            f"Voxel count mismatch: header says {expected_n_voxels}, but found {actual_n_voxels} data lines"
        )
    header = VkVoxelsHeader(
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
        zmin=zmin,
        zmax=zmax,
        nx=nx,
        ny=ny,
        nz=nz,
        novalue=novalue,
    )
    LOGGER.info(f"Loaded voxel header: {header}")
    # create a ndarray of shape (nx, ny, nz, 2) filled with novalue
    # last dimension is (rank, gwb_id)
    voxels = np.full((nx, ny, nz, 2), novalue, dtype=np.int32)
    # parse the voxel data lines, they are in row-major order (x changes fastest)
    for z in range(nz):
        for y in range(ny):
            for x in range(nx):
                line_index = 2 + z * (ny * nx) + y * nx + x
                line = voxels_lines[line_index]
                parts = line.split()
                if len(parts) != 2:
                    raise ValueError(
                        f"Malformed voxel data line {line_index} (expected 2 tokens)"
                    )
                rank, gwb_id = map(int, parts)
                voxels[x, y, z, 0] = rank
                voxels[x, y, z, 1] = gwb_id
    LOGGER.info(f"Loaded voxel grid with shape {voxels.shape}")

    return (header, voxels)


def load_fault(fault_bytes: bytes) -> VkFault:
    # faults are packed as follows:
    # - int32: number of vertices (N)
    # - float32[3*N]: vertex positions (x1, y1, z1, x2, y2, z2, ..., xN, yN, zN)
    # - int32: number of triangles (M)
    # - int32[3*M]: triangle indices (i1_1, i1_2, i1_3, i2_1, i2_2, i2_3, ..., iM_1, iM_2, iM_3)
    data = np.frombuffer(fault_bytes, dtype=np.uint8)
    offset = 0
    n_vertices = int(np.frombuffer(data[offset : offset + 4], dtype=np.int32)[0])
    offset += 4
    vertices = np.frombuffer(
        data[offset : offset + 4 * 3 * n_vertices], dtype=np.float32
    ).reshape((n_vertices, 3))
    offset += 4 * 3 * n_vertices
    n_triangles = int(np.frombuffer(data[offset : offset + 4], dtype=np.int32)[0])
    offset += 4
    triangles = np.frombuffer(
        data[offset : offset + 4 * 3 * n_triangles], dtype=np.int32
    ).reshape((n_triangles, 3))
    offset += 4 * 3 * n_triangles
    if offset != len(data):
        raise ValueError("Malformed fault file, extra data at the end")
    LOGGER.info(f"Loaded fault with {n_vertices} vertices and {n_triangles} triangles")
    return VkFault(vertices=vertices, triangles=triangles)


def read_zip(
    zip_file: ZipFile, simulation_overrides: dict[str, Any] | None = None
) -> VkZipContent:

    # read simulation configuration first
    try:
        with zip_file.open("config.json") as config_file:
            simulation_params = SimulationParameters.model_validate_json(
                config_file.read()
            )
    except KeyError:
        LOGGER.warning(
            "The ZIP file does not contain a config.json file, using default"
        )
        simulation_params = SimulationParameters()

    overrides = simulation_overrides or {}
    if overrides:
        LOGGER.info("Applying command line overrides: %s", overrides)
        simulation_params = simulation_params.model_copy(update=overrides)

    with zip_file.open("project_box.json") as project_box_file:
        vk_project_box = VkProjectBox.model_validate_json(project_box_file.read())

    with zip_file.open("dem_resolution.json") as dem_resolution_file:
        dem_resolution = VkDemResolution.model_validate_json(dem_resolution_file.read())

    with zip_file.open("dem_values.bin") as dem_values_file:
        surface_data_raw = dem_values_file.read()
        LOGGER.info(f"Loaded surface data of length {len(surface_data_raw)} bytes")

    with zip_file.open("stratigraphy.json") as geological_units_file:
        vk_stratigraphy = VkStratigraphy.model_validate_json(
            geological_units_file.read()
        )

    with zip_file.open("voxels.txt") as voxels_file:
        voxels_lines = [
            line.decode("ascii").strip() for line in voxels_file.readlines()
        ]
        vk_voxels_header, vk_voxels = load_voxels(voxels_lines)
        compute_resolution = Point3DInt(
            x=vk_voxels_header.nx, y=vk_voxels_header.ny, z=vk_voxels_header.nz
        )

    with zip_file.open("voxels_units.json") as voxels_units_file:
        vk_voxels_units = VkVoxelsUnits.model_validate_json(voxels_units_file.read())
        LOGGER.info(f"Loaded voxel units: {vk_voxels_units.root}")

    all_files = zip_file.namelist()

    vk_springs: list[VkSpring] = []
    poi_files = filter(lambda x: x.startswith("poi_"), all_files)
    for poi_file in poi_files:
        with zip_file.open(poi_file) as poi_data_file:
            spring = VkSpring.model_validate_json(poi_data_file.read())
            vk_springs.append(spring)
    LOGGER.info(f"Loaded {len(vk_springs)} springs from POI files.")

    vk_gwbs: list[VkGroundwaterBody] = []
    gwb_files = filter(lambda x: x.startswith("gwb_"), all_files)
    for gwb_file in gwb_files:
        with zip_file.open(gwb_file) as gwb_data_file:
            gwb = VkGroundwaterBody.model_validate_json(gwb_data_file.read())
            vk_gwbs.append(gwb)
    LOGGER.info(f"Loaded {len(vk_gwbs)} groundwater bodies from GWB files.")

    vk_faults: list[VkFault] = []
    fault_files = filter(lambda x: x.startswith("fault_"), all_files)
    for fault_file in fault_files:
        with zip_file.open(fault_file) as fault_data_file:
            fault = load_fault(fault_data_file.read())
            vk_faults.append(fault)
    LOGGER.info(f"Loaded {len(vk_faults)} faults from fault files.")

    surface_data = np.frombuffer(surface_data_raw, dtype=np.float32)
    # reshape to 2D array
    surface_data = surface_data.reshape((dem_resolution.n_rows, dem_resolution.n_cols))
    LOGGER.debug(f"Reshaped surface data to {surface_data.shape}")
    # resample to target compute resolution using a bilinear filter
    surface_data = surface_data[
        :: dem_resolution.n_rows // compute_resolution.y,
        :: dem_resolution.n_cols // compute_resolution.x,
    ]
    # flip y axis to have row 0 = min y
    surface_data = np.flipud(surface_data).copy()
    LOGGER.info(f"Resampled surface data to {surface_data.shape}")

    if surface_data.shape[0] < 2 or surface_data.shape[1] < 2:
        raise ValueError("Surface data grid must have at least 2 rows and 2 columns")

    surface_resolution = Point2D(
        x=vk_project_box.width / (surface_data.shape[1] - 1),
        y=vk_project_box.height / (surface_data.shape[0] - 1),
    )
    resampled_dem_resolution = VkDemResolution(
        n_cols=surface_data.shape[1],
        n_rows=surface_data.shape[0],
    )

    return VkZipContent(
        simulation_params=simulation_params,
        project_box=vk_project_box,
        dem_resolution=dem_resolution,
        surface_data=surface_data,
        stratigraphy=vk_stratigraphy,
        compute_resolution=compute_resolution,
        voxels_header=vk_voxels_header,
        voxels=vk_voxels,
        voxels_units=vk_voxels_units,
        faults=vk_faults,
        springs=vk_springs,
        gwbs=vk_gwbs,
        surface_resolution=surface_resolution,
        resampled_dem_resolution=resampled_dem_resolution,
    )
