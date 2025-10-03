import argparse
from pathlib import Path
from typing import Any, Literal

from pykarstnsim_demo.models.io import PyKarstNSimArgs


def _auto_or_float(value: str) -> Literal["auto"] | float:
    if value.lower() == "auto":
        return "auto"
    try:
        return float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Value must be either 'auto' or a number"
        ) from exc


def parse_args() -> PyKarstNSimArgs:
    parser = argparse.ArgumentParser(
        description="Process data exported from VisualKarsys"
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output.txt"),
        help="Path to the output file",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Output intermediate files in a KarstNSim-compatible format",
    )

    parser.add_argument("zip_path", type=Path, help="Path to the input ZIP file")

    parser.add_argument("--name", type=str, default=None, help="Simulation name")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument(
        "--k-pts",
        dest="k_pts",
        type=int,
        default=None,
        help="Number of k-points for the simulation",
    )
    parser.add_argument(
        "--cohesion-factor",
        type=float,
        default=None,
        help="Cohesion factor controlling karst fraction",
    )
    parser.add_argument(
        "--n-sinks",
        type=int,
        default=None,
        help="Number of sinks to generate",
    )
    parser.add_argument(
        "--search-radius",
        type=_auto_or_float,
        default=None,
        help="Neighbor search radius (float) or 'auto'",
    )
    parser.add_argument(
        "--inception-surface-constraint-weight",
        dest="inception_surface_constraint_weight",
        type=float,
        default=None,
        help="Weight applied to inception surface constraints",
    )
    parser.add_argument(
        "--max-inception-surface-distance",
        dest="max_inception_surface_distance",
        type=_auto_or_float,
        default=None,
        help="Maximum distance to inception surface (float) or 'auto'",
    )
    parser.add_argument(
        "--density-sampling-modifier",
        dest="density_sampling_modifier",
        type=float,
        default=None,
        help="Sampling modifier applied in low permeability zones",
    )

    args, _ = parser.parse_known_args()
    zip_path = Path(args.zip_path)
    if not zip_path.is_file() or zip_path.suffix.lower() != ".zip":
        parser.error(f"The file {zip_path} does not exist or is not a ZIP file.")
    overrides: dict[str, Any] = {}
    for field in (
        "name",
        "seed",
        "k_pts",
        "cohesion_factor",
        "n_sinks",
        "search_radius",
        "inception_surface_constraint_weight",
        "max_inception_surface_distance",
        "density_sampling_modifier",
    ):
        value = getattr(args, field)
        if value is not None:
            overrides[field] = value
    return PyKarstNSimArgs(
        zip_path=zip_path,
        output_path=Path(args.output),
        debug=args.debug,
        simulation_overrides=overrides,
    )
