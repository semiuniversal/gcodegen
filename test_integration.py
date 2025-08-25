#!/usr/bin/env python3
"""Integration test for GCodeGen.

This script tests the end-to-end conversion of SVG to G-code.
"""

import os
import sys
import logging
from pathlib import Path

from gcodegen.config import load_config
from gcodegen.cli import convert_svg_to_gcode

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main():
    """Run integration test."""
    # Get script directory
    script_dir = Path(__file__).parent
    
    # Set up test paths
    svg_dir = script_dir / "svg"
    gcode_dir = script_dir / "gcode"
    
    # Create output directory if it doesn't exist
    gcode_dir.mkdir(exist_ok=True)
    
    # Load default configuration
    config = load_config()
    
    # List of test SVG files
    test_files = [
        svg_dir / "scribbles-36.svg",
        svg_dir / "heart-4-5.svg",
    ]
    
    # Process each test file
    for svg_file in test_files:
        if not svg_file.exists():
            logger.error(f"Test file not found: {svg_file}")
            continue
            
        # Generate output file path
        gcode_file = gcode_dir / f"{svg_file.stem}.gcode"
        
        logger.info(f"Converting {svg_file} to {gcode_file}")
        
        # Convert SVG to G-code
        success = convert_svg_to_gcode(svg_file, gcode_file, config)
        
        if success:
            logger.info(f"Successfully converted {svg_file} to {gcode_file}")
            
            # Check if G-code file was created
            if gcode_file.exists():
                logger.info(f"G-code file created: {gcode_file}")
                logger.info(f"G-code file size: {gcode_file.stat().st_size} bytes")
            else:
                logger.error(f"G-code file not created: {gcode_file}")
        else:
            logger.error(f"Failed to convert {svg_file} to {gcode_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 