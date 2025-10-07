import enum

from pydantic import BaseModel


class Permeability(enum.Enum):
    Karstified = "Karstified"
    NonKarstified = "NonKarstified"
    PorousPermeability = "PorousPermeability"
    Undefined = "Undefined"


PERMEABILITY_MAP: dict[Permeability, float] = {
    Permeability.Karstified: 0.5,
    Permeability.NonKarstified: 0.0,
    Permeability.PorousPermeability: 0.0,
    Permeability.Undefined: 0.0,
}


class Point2D(BaseModel):
    x: float
    y: float

    def as_array(self) -> list[float]:
        return [self.x, self.y]


class Point3D(Point2D):
    z: float


class Point3DInt(BaseModel):
    x: int
    y: int
    z: int
