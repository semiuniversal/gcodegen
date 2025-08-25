#!/usr/bin/env python3
"""Test script for the SVG parser module.

This script tests the SVG parser on sample SVG files in the repository.
"""

import argparse
import logging
import sys
from pathlib import Path

from gcodegen.svg import SVGDocument

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("test_svg_parser")


def test_svg_parser(svg_file: Path):
    """Test the SVG parser on a single file.
    
    Args:
        svg_file: Path to SVG file
    """
    logger.info(f"Testing SVG parser on {svg_file}")
    
    try:
        # Parse SVG
        doc = SVGDocument(svg_file)
        
        # Print document info
        logger.info(f"Document dimensions: {doc.width} x {doc.height}")
        logger.info(f"Document viewBox: {doc.viewbox}")
        logger.info(f"Number of paths: {len(doc.paths)}")
        
        # Print path info
        for i, path in enumerate(doc.paths):
            logger.info(f"Path {i+1}:")
            logger.info(f"  Stroke width: {path.stroke_width}")
            logger.info(f"  Stroke color: {path.stroke_color}")
            logger.info(f"  Transform matrix: {path.transform_matrix}")
            
            # Print first few characters of path data
            path_data = path.path_data
            preview = path_data[:50] + "..." if len(path_data) > 50 else path_data
            logger.info(f"  Path data preview: {preview}")
            
            # Test transform on a sample point (10, 10)
            tx, ty = path.transform_point(10, 10)
            logger.info(f"  Transform test (10, 10) -> ({tx:.2f}, {ty:.2f})")
            
        return True
        
    except Exception as e:
        logger.error(f"Error testing SVG parser: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test SVG parser")
    parser.add_argument("svg_file", nargs="?", help="Path to SVG file to test")
    args = parser.parse_args()
    
    # If a specific file is provided, test it
    if args.svg_file:
        test_svg_parser(Path(args.svg_file))
        return
    
    # Otherwise, test all SVG files in the svg directory
    svg_dir = Path(__file__).parent.parent / "svg"
    if not svg_dir.exists():
        logger.error(f"SVG directory not found: {svg_dir}")
        return
        
    logger.info(f"Testing all SVG files in {svg_dir}")
    
    success_count = 0
    failure_count = 0
    
    for svg_file in svg_dir.glob("*.svg"):
        if test_svg_parser(svg_file):
            success_count += 1
        else:
            failure_count += 1
            
    logger.info(f"Test results: {success_count} succeeded, {failure_count} failed")


if __name__ == "__main__":
    main() 