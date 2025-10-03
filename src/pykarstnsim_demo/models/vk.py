from dataclasses import dataclass

import numpy as np
from pydantic import BaseModel, ConfigDict, RootModel
from pydantic.alias_generators import to_camel

from pykarstnsim_demo.models.shared import Permeability, Point3D, Point3DInt


class VkProjectBox(BaseModel):
    width: float
    height: float
    min_elevation: float
    max_elevation: float

    @property
    def depth(self) -> float:
        return self.max_elevation - self.min_elevation


class VkDemResolution(BaseModel):
    n_cols: int
    n_rows: int


class VkGeologicalUnit(BaseModel):

    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)

    name: str  # for display only
    permeability: Permeability
    strati_unit_id: int


VkStratigraphy = RootModel[list[VkGeologicalUnit]]


class VkSpring(Point3D):
    poi_id: int
    catchment: list[tuple[float, float]]


class VkVoxelsHeader(BaseModel):
    xmin: float
    xmax: float
    ymin: float
    ymax: float
    zmin: float
    zmax: float
    nx: int
    ny: int
    nz: int
    novalue: int


VkVoxelsUnits = RootModel[list[int]]


class VkGroundwaterBody(BaseModel):
    gwb_id: int
    spring_id: int


@dataclass
class VkFault:

    vertices: np.ndarray  # shape (n, 3)
    triangles: np.ndarray  # shape (m, 3)
