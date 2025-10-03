# PyKarstNSim Demo

A demonstration tool for generating 3D karst networks from data exported from [Visual KARSYS](https://www.visualkarsys.com/).

## About

This project provides a command-line interface to process Visual KARSYS project exports and generate realistic 3D karst network simulations using [PyKarstNSim](https://github.com/ISSKA/pykarstnsim).

### What is Visual KARSYS?

Visual KARSYS is a software platform dedicated to karst groundwater management. It offers a series of tools for assessing aquifer geometries and groundwater flow-systems.

Visual KARSYS is made available for scientists, engineers, managers and stakeholders facing environmental issues in karst environments:

- groundwater resources exploitation and protection
- civil engineering projects
- geothermal heat probes
- natural hazards
- waste deposits
- etc.

This tool allows you to export your Visual KARSYS project data and use it to generate detailed 3D karst network simulations using the powerful [KarstNSim](https://github.com/ring-team/KarstNSim_Public) algorithm.

## Quick start

### Option 1: Using [uv](https://docs.astral.sh/uv/) (recommended)

```bash
# Clone the repository
git clone https://github.com/ISSKA/pykarstnsim-demo.git
cd pykarstnsim-demo

# Run directly with uv (will install dependencies automatically)
uv run demo.py example/example.zip
```

### Option 2: Using pip

```bash
# Clone the repository
git clone https://github.com/ISSKA/pykarstnsim-demo.git
cd pykarstnsim-demo

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install the package
pip install -e .
# Run the demo
python demo.py example/example.zip
```

## Usage

### Running the Example

An example Visual KARSYS export is provided in the `example/` directory:

**Using uv:**
```bash
uv run python demo.py example/example.zip
```

**Using pip (with activated virtual environment):**
```bash
python demo.py example/example.zip
```

By default, results will be saved to `output.txt`. You can specify a custom output path with the `-o` option.

## CLI Arguments

### Required Arguments

- `zip_path` - Path to the Visual KARSYS export ZIP file

### Optional Arguments

#### General Options

- `-o`, `--output` - Path to the output file (default: `output.txt`)
- `--debug` - Output intermediate files in a KarstNSim-compatible format

#### Simulation Parameters

These parameters allow you to override settings from the Visual KARSYS export:

- `--name` - Simulation name
- `--seed` - Random seed for reproducible results
- `--k-pts` - Number of k-points for the simulation (controls network complexity)
- `--cohesion-factor` - Cohesion factor controlling karst fraction (0.0-1.0)
- `--n-sinks` - Number of sinks to generate
- `--search-radius` - Neighbor search radius (float or 'auto')
- `--inception-surface-constraint-weight` - Weight applied to inception surface constraints
- `--max-inception-surface-distance` - Maximum distance to inception surface (float or 'auto')
- `--density-sampling-modifier` - Sampling modifier applied in low permeability zones

### Examples

Generate a simulation with a specific seed and output file:
```bash
uv run python demo.py example/example.zip --seed 42 -o my_results.txt
```

Override multiple simulation parameters:
```bash
uv run python demo.py example/example.zip \
    --k-pts 20 \
    --cohesion-factor 0.95 \
    --n-sinks 200 \
    --seed 123 \
    -o results/simulation_001.txt
```

Enable debug mode to output intermediate files:
```bash
uv run python demo.py example/example.zip --debug
# will create debug_...txt files in the current directory
```

## Output

The tool generates text files containing the simulated karst network geometry. These output files can be:

- **Reimported into Visual KARSYS** (for licensed users only) - Use the KarstNSim step in the Visual KARSYS wizard to export/import your generated karst networks back into your project for further analysis and visualization
- Used with other visualization and analysis tools
- Further processed or analyzed using custom scripts

The output format is compatible with the Visual KARSYS import workflow, enabling a complete round-trip from Visual KARSYS export → KarstNSim simulation → Visual KARSYS import.

## Dependencies

This project depends on:

- [PyKarstNSim](https://github.com/ISSKA/pykarstnsim) - Python bindings for KarstNSim
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Shapely](https://shapely.readthedocs.io/) - Geometric operations

## Citation

If you use this tool in your research, please cite the original KarstNSim publication:

```bibtex
@article{Gouy2024,
    author = {Gouy, Augustin and Collon, Pauline and Bailly-Comte, Vincent and Galin, Eric and Antoine, Christophe and Thebault, Benoît and Landrein, Philippe},
    doi = {10.1016/j.jhydrol.2024.130878},
    journal = {Journal of Hydrology},
    title = {{KarstNSim: A graph-based method for 3D geologically-driven simulation of karst networks}},
    year = {2024}
}
```

## Documentation

For more information about the underlying simulation methodology and parameters:

- **PyKarstNSim**: https://github.com/ISSKA/pykarstnsim
- **KarstNSim**: https://github.com/ring-team/KarstNSim_Public
- **Config Reference**: https://github.com/ISSKA/KarstNSim_Public/blob/main/config_reference.md
- **Visual KARSYS**: https://www.visualkarsys.com/

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Setup

To upgrade the PyKarstNSim dependency to the latest version:

```bash
uv sync --upgrade
```

### Editor Configuration

Default VSCode settings are provided in `.vscode/settings.json.default`. Contributors can rename this file to `.vscode/settings.json` to use the project's default enforced options for consistent development experience.

## Contact

For questions or issues, please open an issue on this repository or contact the [SISKA (Swiss Institute for Speleology and Karst Studies)](https://www.isska.ch).

## Debug Viewer

The project includes a self-contained `debug_viewer.html` file that allows you to visualize and interact with the debug files generated by the tool. This viewer is particularly useful for inspecting intermediate outputs and understanding the simulation results, without needing to reimport them into Visual KARSYS.

### Usage

1. Open the `debug_viewer.html` file in any modern web browser.
2. Use the file input fields to load the desired debug files:
   - **Output File**: Load the main output file (e.g., `debug_output.txt`).
   - **Surface File**: Load the DEM file (e.g., `debug_surface.txt`).
   - **Watertable/Inception Surface Files**: Load one or more watertable or inception surface files.
   - **Springs and Sinks Files**: Load `debug_springs.txt` and `debug_sinks.txt`.
   - (optional) **Project Box File**: Load the project box file (e.g., `debug_project_box.txt`).
3. Interact with the 3D scene using mouse controls:
   - **Orbit**: Left-click and drag.
   - **Zoom**: Scroll wheel.
   - **Pan**: Right-click and drag.
4. Use the UI controls to customize the visualization:
   - Toggle visibility of elements like axes, grid, and project box.

### Example Workflow

1. Run the tool in debug mode to generate intermediate files:
   ```bash
   uv run demo.py example/example.zip --debug
   ```
2. Open `debug_viewer.html` in your browser.
3. Load the generated debug files to inspect the simulation results.

The `debug_viewer.html` file is located in the root directory of the project. It is a standalone tool and does not require any additional setup or dependencies.
