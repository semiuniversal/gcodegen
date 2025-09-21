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

### Operator quick-start

- Adjust only these knobs per tool:
  - `viscosity` (0.00 water, 0.50 milk, 1.00 heavy cream)
  - `flow_offset` small nudge (±0.02); `flow_scale` 0.9–1.2 bigger nudge
  - `v_min`/`v_max` to shift overall speed range
- Drips → lower `viscosity` or `flow_offset` slightly; maybe raise `v_max`.
- Starved flow → raise `viscosity` or `flow_offset`; maybe lower `v_min`.

### Calibration pattern

An 8.5x11in calibration SVG is provided at `svg/calibration-letter.svg` (width and opacity ladders). Convert it like this:

```bash
uv run gcodegen --input svg/calibration-letter.svg --output gcode/calibration-letter.gcode --config config.yaml
```

For calibrating Tool 1 (Brush B, white ink), use the white variant and print on a dark surface for contrast (e.g., colored printer paper or black construction paper):

```bash
uv run gcodegen --input svg/calibration-letter-white.svg --output gcode/calibration-letter-white.gcode --config config.yaml
```

## Development

This project uses:
- Python 3.8+
- lxml for SVG parsing
- numpy for geometry operations
- pyyaml for configuration

## License

MIT
