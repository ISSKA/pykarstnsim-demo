import logging

import numpy as np
from pykarstnsim.models import ConnectivityMatrix, ConnectivityType, Sink
from shapely import Point, Polygon

from pykarstnsim_demo.models.shared import Point2D
from pykarstnsim_demo.models.vk import VkDemResolution, VkSpring

LOGGER = logging.getLogger(__name__)


def load_sinks(
    n_sinks: int,
    springs: list[VkSpring],
    dem_resolution: VkDemResolution,
    surface_resolution: Point2D,
    surface_data: np.ndarray,
    rng: np.random.Generator,
    num_springs: int,
) -> tuple[list[Sink], ConnectivityMatrix]:

    def random_points_in_polygon(poly: Polygon, n_points: int) -> np.ndarray:
        """Uniform random points inside a polygon via rejection sampling."""

        if n_points <= 0:
            return np.empty((0, 2), dtype=np.float64)

        minx, miny, maxx, maxy = poly.bounds

        accepted: list[tuple[float, float]] = []
        remaining = n_points
        # heuristic: batch size = 2x remaining (increase if polygon occupies small fraction)
        while remaining > 0:
            batch_size = max(remaining * 2, 32)
            xs = rng.uniform(minx, maxx, size=batch_size)
            ys = rng.uniform(miny, maxy, size=batch_size)
            for x, y in zip(xs, ys):
                if poly.covers(Point(x, y)):
                    accepted.append((x, y))
                    remaining -= 1
                    if remaining == 0:
                        break
        pts = np.asarray(accepted, dtype=np.float64)
        return pts

    def elevation_at_xy(x: float, y: float) -> float:
        """Bilinear interpolation of elevation at given (x,y) in local box coordinates"""
        # convert to grid indices
        col = x / surface_resolution.x
        row = y / surface_resolution.y
        if (
            col < 0
            or col >= dem_resolution.n_cols - 1
            or row < 0
            or row >= dem_resolution.n_rows - 1
        ):
            raise ValueError(f"Point ({x},{y}) out of DEM bounds")
        col0 = int(np.floor(col))
        row0 = int(np.floor(row))
        col1 = col0 + 1
        row1 = row0 + 1
        # fractional part
        dc = col - col0
        dr = row - row0
        # bilinear interpolation
        z00 = surface_data[row0, col0]
        z10 = surface_data[row0, col1]
        z01 = surface_data[row1, col0]
        z11 = surface_data[row1, col1]
        z0 = z00 * (1 - dc) + z10 * dc
        z1 = z01 * (1 - dc) + z11 * dc
        z = z0 * (1 - dr) + z1 * dr
        return float(z)

    if n_sinks <= 0:
        empty_matrix = ConnectivityMatrix([])
        return [], empty_matrix

    catchment_ids: list[str | int] = []
    catchment_polygons: list[Polygon] = []
    for spring in springs:
        coords = np.array(spring.catchment, dtype=np.float64)
        polygon = Polygon(coords)
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
        catchment_ids.append(spring.poi_id)
        catchment_polygons.append(polygon)

    areas = np.array([poly.area for poly in catchment_polygons], dtype=np.float64)
    if np.all(areas == 0):
        weights = np.full(len(catchment_polygons), 1.0 / len(catchment_polygons))
    else:
        weights = areas / areas.sum()

    if len(catchment_polygons) == 1:
        assignments = np.zeros(n_sinks, dtype=int)
    else:
        # get random assignments of sinks to catchments based on weights
        assignments = rng.choice(len(catchment_polygons), size=n_sinks, p=weights)
    counts = np.bincount(assignments, minlength=len(catchment_polygons))

    sinks: list[Sink] = []
    connectivity_matrix_data: list[list[ConnectivityType]] = []
    sink_index = 1
    for idx, (spring_id, polygon) in enumerate(zip(catchment_ids, catchment_polygons)):
        count = int(counts[idx])
        if count == 0:
            continue
        LOGGER.info(
            "Allocating %d sinks to spring %s catchment (area=%.2f)",
            count,
            spring_id,
            areas[idx],
        )
        sinks_pts = random_points_in_polygon(polygon, count)
        for x, y in sinks_pts:
            sinks.append(
                Sink(
                    origin=(float(x), float(y), elevation_at_xy(float(x), float(y))),
                    index=sink_index,
                    order=1,
                    radius=0.0,
                )
            )
            # Create connectivity row for this sink
            row = [ConnectivityType.NOT_CONNECTED] * num_springs
            row[idx] = ConnectivityType.CONNECTED  # idx is the spring index
            connectivity_matrix_data.append(row)
            sink_index += 1

    connectivity_matrix = ConnectivityMatrix(connectivity_matrix_data)
    return sinks, connectivity_matrix
