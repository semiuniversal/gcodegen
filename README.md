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

### Troubleshooting

- Starts of lines look faint or delayed:
  - Increase `airbrush.paint_lead_ms` (e.g., 80–120). This adds a short delay after pre-opening paint before XY motion.
  - Ensure feedrate is set at stroke start; the generator does this automatically.
- End of lines leave a splotch:
  - The generator ramps paint flow down on the final segment. If blot persists, slightly decrease `svg.max_segment_length_mm` (e.g., from 1.5 → 1.0) so ramp-down spans a shorter segment.
- Shaky motion or “fast jumps” while painting curves:
  - Increase sampling density: raise `svg.curve_resolution` (e.g., 24 → 36) and/or reduce `svg.max_segment_length_mm` (e.g., 1.5 → 0.8).
- Width/opacity don’t match expectations:
  - Adjust per-tool `viscosity`, `flow_scale`, and `flow_offset`. Lower viscosity for thinner paints; raise for thicker.
- Viewer doesn’t show continuous strokes (if visualizing the gcode with tools like ncviewer.com):
  - Enable `airbrush.viewer_compat: true` to keep U/V off XY lines (more viewer-friendly). Optional: `airbrush.viewer_emit_m3m5: true` to add M3/M5 hints for cutting visualization. These do not change machine behavior.

Regenerate shipped G-code after config changes to ensure consistency before printing.


## Development

This project uses:
- Python 3.8+
- lxml for SVG parsing
- numpy for geometry operations
- pyyaml for configuration

## License

MIT
