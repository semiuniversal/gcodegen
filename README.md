# GCodeGen

A CLI tool to convert simplified SVGs into G-code for the H.Airbrush device.

## Overview

GCodeGen is a command-line tool that converts SVG files (containing only straight lines) into G-code optimized for the H.Airbrush hardware. It reuses concepts from the previous Inkscape extension but operates independently without Inkscape dependencies.

## Features

- SVG → G-code pipeline without Inkscape
- Support for straight lines with width interpretation
- Black/white color switching
- Hardware-specific transforms and offsets
- Duet 2 WiFi compatible G-code output

## Installation

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

## Usage

```bash
gcodegen --input path/to/file.svg --output path/to/output.gcode --config path/to/config.yaml
```

## Development

This project uses:
- Python 3.8+
- lxml for SVG parsing
- numpy for geometry operations
- pyyaml for configuration

## License

MIT
