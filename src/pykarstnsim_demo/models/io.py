import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from pykarstnsim.models import KarstNSimResult

from pykarstnsim_demo.models.shared import Point3DInt


class SimulationParameters(BaseModel):
    """
    Parameters exposed to the user for configuring the simulation.
    """

    # JSON comes from VisualKarsys with camelCase keys
    model_config = ConfigDict(alias_generator=to_camel)

    name: str = "Karst Network"
    seed: int = 42
    k_pts: int = 10
    cohesion_factor: float = 0.9
    n_sinks: int = 100
    search_radius: Literal["auto"] | float = "auto"
    inception_surface_constraint_weight: float = 1.0
    max_inception_surface_distance: Literal["auto"] | float = "auto"
    density_sampling_modifier: float = 2.0
    """How should sampling be affected by permeability? 1.0 = no effect, > 1.0 = more points in permable areas"""


class PyKarstNSimArgs(BaseModel):
    zip_path: Path
    output_path: Path
    debug: bool
    simulation_overrides: dict[str, Any]


@dataclass
class OutputFormat:
    config: SimulationParameters
    result: KarstNSimResult

    def to_string(
        self,
        runtime_s: float,
        generation_time: datetime,
        compute_resolution: Point3DInt,
    ) -> str:
        lines = ["# Run info"]
        lines.append(
            json.dumps(
                {
                    "metadata": {
                        "generationTime": generation_time.isoformat(),
                        "generationDurationS": runtime_s,
                        "computeResolution": {
                            "x": compute_resolution.x,
                            "y": compute_resolution.y,
                            "z": compute_resolution.z,
                        },
                    },
                    "config": self.config.model_dump(by_alias=True),
                },
                indent=2,
            )
        )
        lines.append("# Data")
        lines.append(self.result.to_string())
        return "\n".join(lines)
