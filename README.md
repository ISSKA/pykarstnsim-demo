# PyKarstNSim Demo

A bridge tool for generating 3D karst networks from [Visual KARSYS](https://www.visualkarsys.com/) exports using [PyKarstNSim](https://github.com/ISSKA/pykarstnsim).

## Overview

This tool enables a complete workflow for 3D karst network simulation:

```
Visual KARSYS → Export ZIP → KarstNSim Simulation → Import Results → Visual KARSYS
     (setup)                  (this tool)              (analysis)
```

### The Workflow

1. **Export from Visual KARSYS**: Use the KarstNSim wizard step in Visual KARSYS to export your project data as a ZIP file
2. **Run Simulation**: Process the ZIP file with this tool to generate 3D karst network simulations
3. **Import Results**: Load the output back into Visual KARSYS for visualization and analysis, or use the standalone debug viewer

### What is Visual KARSYS?

Visual KARSYS is a software platform dedicated to karst groundwater management. It offers a series of tools for assessing aquifer geometries and groundwater flow-systems.

Visual KARSYS is made available for scientists, engineers, managers and stakeholders facing environmental issues in karst environments:

- groundwater resources exploitation and protection
- civil engineering projects
- geothermal heat probes
- natural hazards
- waste deposits
- etc.

This tool acts as the computational engine for Visual KARSYS's KarstNSim workflow, leveraging the powerful [KarstNSim](https://github.com/ring-team/KarstNSim_Public) algorithm to generate realistic 3D karst conduit networks.

Both this tool and Visual KARSYS are developed and maintained by [SISKA (Swiss Institute for Speleology and Karst Studies)](https://www.isska.ch).

> **Note for Visual KARSYS Users**: The KarstNSim feature currently requires a specific license tier. If you're already using Visual KARSYS and are interested in trying this tool, please contact us at [info@visualkarsys.com](mailto:info@visualkarsys.com) to discuss access. This license requirement is temporary while the feature is being stabilized and will be more widely available once fully integrated into Visual KARSYS.

## Quick Start

This repository serves as both a **demonstration** (try the example) and a **production tool** (process your own Visual KARSYS exports).

### Try the Demo

An example Visual KARSYS export is included to help you understand the workflow:

**Using [uv](https://docs.astral.sh/uv/) (recommended):**

```bash
# Clone the repository
git clone https://github.com/ISSKA/pykarstnsim-demo.git
cd pykarstnsim-demo

# Run the example directly (dependencies installed automatically)
uv run demo.py example/example.zip
```

**Using pip:**

```bash
# Clone the repository
git clone https://github.com/ISSKA/pykarstnsim-demo.git
cd pykarstnsim-demo

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# Run the example
python demo.py example/example.zip
```

This generates `output.txt` containing the simulated karst network.

### Process Your Own Data

#### Step 1: Export from Visual KARSYS

1. Open your project in Visual KARSYS
2. Navigate to the **KarstNSim wizard step** (licensed version required)
3. Configure your simulation parameters
4. **Export** your project as a ZIP file

#### Step 2: Run the Simulation

```bash
uv run demo.py path/to/your_export.zip -o results/my_karst_network.txt
```

You can override any export parameters using CLI flags (see [CLI Arguments](#cli-arguments) below).

#### Step 3: Import Back to Visual KARSYS

1. Return to the **KarstNSim wizard step** in Visual KARSYS
2. **Import** the generated output file (`my_karst_network.txt`)
3. Visualize and analyze your 3D karst network

**Alternative**: Use the standalone [debug viewer](#debug-viewer) (no Visual KARSYS license needed).


## Advanced Usage

### CLI Arguments

The tool accepts Visual KARSYS ZIP exports and allows parameter overrides for experimentation.

### Required Arguments

- `zip_path` - Path to the Visual KARSYS export ZIP file

### Optional Arguments

#### General Options

- `-o`, `--output` - Path to the output file (default: `output.txt`)
- `--debug` - Generate intermediate debug files for inspection (enables use of debug viewer)

#### Simulation Parameters (Override Export Settings)

These parameters let you experiment with different settings without re-exporting from Visual KARSYS:

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

**Basic usage with custom output:**
```bash
uv run demo.py example/example.zip -o results/simulation_001.txt
```

**Override parameters for experimentation:**
```bash
uv run demo.py example/example.zip \
    --k-pts 20 \
    --cohesion-factor 0.95 \
    --n-sinks 200 \
    --seed 123 \
    -o results/experiment_high_density.txt
```

**Enable debug mode for inspection:**
```bash
uv run demo.py example/example.zip --debug
# Generates debug_*.txt files that can be loaded in debug_viewer.html
```

## Visualizing Results

### Option 1: Visual KARSYS (Recommended)

**For licensed Visual KARSYS users:**

1. Open your project in Visual KARSYS
2. Navigate to the KarstNSim wizard step
3. Paste the content of the output file into the import field
4. Visualize and analyze the 3D karst network with full Visual KARSYS capabilities

This is the primary workflow for production use.

### Option 2: Standalone Debug Viewer

**For users without Visual KARSYS or quick inspection:**

The included `debug_viewer.html` provides interactive 3D visualization without requiring Visual KARSYS.

#### Usage

1. Run the tool with `--debug` flag to generate intermediate files:
   ```bash
   uv run demo.py example/example.zip --debug
   ```

2. Open `debug_viewer.html` in any modern web browser

3. Load the generated debug files using the file input fields:
   - **Output File**: `debug_output.txt` (main karst network)
   - **Surface File**: `debug_surface.txt` (terrain DEM)
   - **Watertable/Inception Surfaces**: `debug_water_table_*.txt`, `debug_inception_surface_*.txt`
   - **Springs and Sinks**: `debug_springs.txt`, `debug_sinks.txt`
   - **Project Box** (optional): `debug_project_box.txt`

4. Interact with the 3D scene:
   - **Orbit**: Left-click and drag
   - **Zoom**: Scroll wheel
   - **Pan**: Right-click and drag
   - **Toggle elements**: Use UI controls to show/hide axes, grid, project box, etc.

The debug viewer is a standalone HTML file requiring no installation or dependencies.

## Technical Details

### Dependencies

This project depends on:

- [PyKarstNSim](https://github.com/ISSKA/pykarstnsim) - Python bindings for KarstNSim
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Shapely](https://shapely.readthedocs.io/) - Geometric operations

### Output Format

The tool generates text files in a format compatible with Visual KARSYS's KarstNSim import function. These files contain:

- 3D karst conduit network geometry
- Node positions and connectivity
- Metadata for integration with Visual KARSYS projects

For more details on the underlying algorithm and configuration options:

- **PyKarstNSim**: https://github.com/ISSKA/pykarstnsim
- **KarstNSim**: https://github.com/ring-team/KarstNSim_Public
- **Config Reference**: https://github.com/ISSKA/KarstNSim_Public/blob/main/config_reference.md

### Citation

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

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Setup

Clone the repository and set up the development environment:

```bash
git clone https://github.com/ISSKA/pykarstnsim-demo.git
cd pykarstnsim-demo
uv sync
```

To upgrade the PyKarstNSim dependency to the latest version:

```bash
uv sync --upgrade
```

### Editor Configuration

Default VSCode settings are provided in `.vscode/settings.json.default`. Contributors can rename this file to `.vscode/settings.json` to use the project's default settings for a consistent development experience.

## Support

- **Questions or Issues**: Open an issue on this repository
- **Visual KARSYS Support**: Contact us at [info@visualkarsys.com](mailto:info@visualkarsys.com)
- **SISKA**: [Swiss Institute for Speleology and Karst Studies](https://www.isska.ch)
- **Visual KARSYS Website**: https://www.visualkarsys.com/

## License

See [LICENSE](LICENSE) file for details.
