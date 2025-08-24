"""Command-line interface for GCodeGen."""

import argparse
import sys
from pathlib import Path

from . import __version__


def parse_args(args=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert SVG files to G-code for H.Airbrush device."
    )
    parser.add_argument(
        "--input", "-i", required=True, type=Path, help="Input SVG file path"
    )
    parser.add_argument(
        "--output", "-o", required=True, type=Path, help="Output G-code file path"
    )
    parser.add_argument(
        "--config", "-c", type=Path, help="Configuration YAML file path"
    )
    parser.add_argument(
        "--units",
        choices=["mm", "in"],
        default="mm",
        help="Units to use (default: mm)",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    
    return parser.parse_args(args)


def main():
    """Main entry point for the CLI."""
    args = parse_args()
    
    # Validate input file
    if not args.input.exists():
        print(f"Error: Input file '{args.input}' does not exist.", file=sys.stderr)
        return 1
    
    # Validate config file if provided
    if args.config and not args.config.exists():
        print(f"Error: Config file '{args.config}' does not exist.", file=sys.stderr)
        return 1
    
    # Create output directory if it doesn't exist
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Converting {args.input} to {args.output} using units: {args.units}")
    if args.config:
        print(f"Using config file: {args.config}")
    
    # TODO: Implement actual conversion logic
    print("Conversion not yet implemented.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 