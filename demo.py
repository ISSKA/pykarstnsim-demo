import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import numpy as np
from pykarstnsim.config import KarstConfig
from pykarstnsim.karstnsim import run_simulation
from pykarstnsim.models.sink import Sink
from pykarstnsim.models.spring import Spring
from pykarstnsim.models.surface import Surface

from pykarstnsim_demo.cli import parse_args
from pykarstnsim_demo.converters.project_box import load_project_box
from pykarstnsim_demo.converters.sinks import load_sinks
from pykarstnsim_demo.converters.water_tables import load_water_tables
from pykarstnsim_demo.models.io import OutputFormat
from pykarstnsim_demo.vkzipreader import read_zip

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


def main(
    zip_file: ZipFile,
    output_path: Path,
    debug: bool,
    simulation_overrides: dict[str, Any] | None = None,
):

    vk_project = read_zip(zip_file, simulation_overrides)

    project_box = load_project_box(
        vk_project.project_box,
        vk_project.stratigraphy,
        vk_project.compute_resolution,
        vk_project.voxels,
        vk_project.voxels_units.root,
        vk_project.simulation_params.r_min_pervious,
        vk_project.simulation_params.r_min_impervious,
    )
    dem = Surface.from_dem_grid(
        vk_project.surface_data,
        vk_project.project_box.width,
        vk_project.project_box.height,
    )
    springs = [
        Spring(
            origin=(s.x, s.y, s.z),
            index=i + 1,  # 1-based index (maybe use spring_id?)
            water_table_index=0,  # set below
            radius=0.0,
        )
        for i, s in enumerate(vk_project.springs)
    ]

    # dict: vk gwb_id -> water table surface
    gwb_surfaces = load_water_tables(vk_project.voxels, vk_project.project_box)
    ordered_gwb_ids = sorted(gwb_surfaces.keys())
    water_tables: list[Surface] = [gwb_surfaces[gwb_id] for gwb_id in ordered_gwb_ids]
    # dict: vk spring_id -> water table index (1-based)
    spring_to_wt_index: dict[int, int] = {}
    for wt_index, gwb_id in enumerate(ordered_gwb_ids, start=1):
        for gwb in vk_project.gwbs:
            if gwb.gwb_id == gwb_id:
                spring_to_wt_index[gwb.spring_id] = wt_index
    # assign water table index to each spring
    for spring, vk_spring in zip(springs, vk_project.springs):
        if vk_spring.poi_id in spring_to_wt_index:
            spring.water_table_index = spring_to_wt_index[vk_spring.poi_id]
        else:
            LOGGER.fatal(
                f"Spring at {spring.origin} (index {spring.index}) has no associated groundwater body."
            )
            exit(1)

    # sanity check: all springs should have a water table assigned
    for spring in springs:
        if spring.water_table_index == 0:
            LOGGER.fatal(
                f"Spring at {spring.origin} (index {spring.index}) has no water table assigned."
            )
            exit(1)

    # faults
    faults: list[Surface] = [
        Surface.from_vertices_and_triangles(f.vertices, f.triangles)
        for f in vk_project.faults
    ]
    LOGGER.info(f"Loaded {len(faults)} inception surfaces.")

    # rng matching simulation seed
    rng = np.random.default_rng(vk_project.simulation_params.seed)

    # sinks
    sinks, connectivity_matrix = load_sinks(
        vk_project.simulation_params.n_sinks,
        vk_project.springs,
        vk_project.resampled_dem_resolution,
        vk_project.surface_resolution,
        vk_project.surface_data,
        rng,
        len(springs),
    )

    if debug:
        Path("debug_surface.txt").write_text(dem.to_string())
        Path("debug_sinks.txt").write_text(Sink.to_string(sinks))
        for i in range(len(faults)):
            Path(f"debug_inception_surface_{i+1}.txt").write_text(faults[i].to_string())
        Path("debug_project_box.txt").write_text(project_box.to_string())
        Path("debug_springs.txt").write_text(Spring.to_string(springs))
        Path("debug_connectivity_matrix.txt").write_text(
            connectivity_matrix.to_string()
        )
        for i in range(len(water_tables)):
            Path(f"debug_water_table_{i+1}.txt").write_text(water_tables[i].to_string())

    LOGGER.info(
        f"Simulation configuration: {vk_project.simulation_params.model_dump_json(indent=2)}"
    )

    max_dim = max(
        vk_project.project_box.width / vk_project.compute_resolution.x,
        vk_project.project_box.height / vk_project.compute_resolution.y,
        vk_project.project_box.depth / vk_project.compute_resolution.z,
    )

    config = KarstConfig()
    config.karstic_network_name = vk_project.simulation_params.name
    config.selected_seed = vk_project.simulation_params.seed
    config.k_pts = vk_project.simulation_params.k_pts
    config.fraction_karst_perm = vk_project.simulation_params.cohesion_factor
    if vk_project.simulation_params.search_radius == "auto":
        config.nghb_radius = max_dim * 3.0
        LOGGER.info(f"Auto-setting neighbor search radius to {config.nghb_radius:.2f}")
    else:
        config.nghb_radius = vk_project.simulation_params.search_radius
    config.inception_surface_constraint_weight = (
        vk_project.simulation_params.inception_surface_constraint_weight
    )
    if vk_project.simulation_params.max_inception_surface_distance == "auto":
        config.max_inception_surface_distance = max_dim * 3.0
        LOGGER.info(
            f"Auto-setting max inception surface distance to {config.max_inception_surface_distance:.2f}"
        )
    else:
        config.max_inception_surface_distance = (
            vk_project.simulation_params.max_inception_surface_distance
        )

    # static overrides
    config.use_max_nghb_radius = True
    config.refine_surface_sampling = 1  # refine 1 time
    config.use_karstification_potential = True
    config.karstification_potential_weight = 1.0
    config.nb_deadend_points = 0

    LOGGER.info(f"Starting simulation with size {vk_project.compute_resolution}")

    config.create_vset_sampling = debug

    start_time = time.time_ns()
    res = run_simulation(
        config,
        project_box=project_box,
        sinks=sinks,
        springs=springs,
        connectivity_matrix=connectivity_matrix,
        water_tables=water_tables,
        topo_surface=dem,
        inception_surfaces=faults,
    )
    end_time = time.time_ns()
    runtime_s = (end_time - start_time) / 1e9
    generation_time = datetime.now()

    if res is None:
        LOGGER.error("Simulation failed, no result returned.")
        exit(1)

    LOGGER.info("Simulation completed successfully in %.2f seconds.", runtime_s)
    LOGGER.info(f"Number of generated segments: {len(res.segments)}")

    if debug:
        Path("debug_output.txt").write_text(res.to_string())
    output = OutputFormat(vk_project.simulation_params, res)
    output_path.write_text(
        output.to_string(
            runtime_s,
            generation_time,
            vk_project.compute_resolution,
        )
    )

    LOGGER.info(f"Results written to {output_path}")


if __name__ == "__main__":
    args = parse_args()
    with ZipFile(args.zip_path, "r") as zip_file:
        main(zip_file, args.output_path, args.debug, args.simulation_overrides)
