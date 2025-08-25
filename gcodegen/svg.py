"""SVG parsing module for GCodeGen.

This module handles parsing SVG files, extracting path data, and normalizing
coordinates for G-code generation. It supports both direct paths and paths
within transform groups.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from lxml import etree

# Set up logging
logger = logging.getLogger(__name__)

# SVG namespace
SVG_NS = "{http://www.w3.org/2000/svg}"


class SVGDocument:
    """Class for handling SVG document parsing and data extraction."""

    def __init__(self, file_path: Union[str, Path]):
        """Initialize SVG document from file.

        Args:
            file_path: Path to SVG file
        """
        self.file_path = Path(file_path)
        self.tree = None
        self.root = None
        self.width = 0
        self.height = 0
        self.viewbox = (0, 0, 0, 0)
        self.paths = []
        
        self._parse()
        
    def _parse(self):
        """Parse the SVG file and extract basic document properties."""
        try:
            self.tree = etree.parse(str(self.file_path))
            self.root = self.tree.getroot()
            
            # Extract document dimensions
            width = self.root.get("width")
            height = self.root.get("height")
            
            # Handle units (px, mm, etc.)
            self.width = self._parse_dimension(width)
            self.height = self._parse_dimension(height)
            
            # Extract viewBox if available
            viewbox = self.root.get("viewBox")
            if viewbox:
                self.viewbox = tuple(map(float, viewbox.split()))
            else:
                self.viewbox = (0, 0, self.width, self.height)
                
            # Extract paths
            self._extract_paths()
            
        except Exception as e:
            logger.error(f"Error parsing SVG file {self.file_path}: {e}")
            raise
            
    def _parse_dimension(self, value: Optional[str]) -> float:
        """Parse dimension value with optional units.
        
        Args:
            value: Dimension string (e.g., "100px", "10mm")
            
        Returns:
            Parsed value as float (in pixels)
        """
        if not value:
            return 0.0
            
        # Remove units for now - will add proper unit conversion later
        value = value.strip()
        for unit in ["px", "pt", "mm", "cm", "in"]:
            if value.endswith(unit):
                value = value[:-len(unit)]
                break
                
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Could not parse dimension: {value}")
            return 0.0
            
    def _extract_paths(self):
        """Extract all path elements from the SVG document."""
        # First, find all direct path elements
        path_elements = self.root.findall(f".//{SVG_NS}path")
        
        # Process each path
        for path_elem in path_elements:
            path = SVGPath(path_elem)
            
            # Find parent transforms
            transform_chain = []
            parent = path_elem.getparent()
            while parent is not None and parent != self.root:
                if parent.get("transform"):
                    transform_chain.append(parent.get("transform"))
                parent = parent.getparent()
                
            # Apply transforms in reverse order (innermost last)
            transform_chain.reverse()
            for transform in transform_chain:
                path.add_transform(transform)
                
            self.paths.append(path)
            
        logger.info(f"Extracted {len(self.paths)} paths from SVG")
        
    def get_paths(self) -> List['SVGPath']:
        """Get all paths from the document.
        
        Returns:
            List of SVGPath objects
        """
        return self.paths


class SVGPath:
    """Class representing an SVG path element with its data and transforms."""
    
    def __init__(self, path_element):
        """Initialize from an SVG path element.
        
        Args:
            path_element: lxml Element for the path
        """
        self.element = path_element
        self.path_data = path_element.get("d", "")
        self.transform_matrix = np.identity(3)  # Identity matrix
        self.style = self._parse_style(path_element.get("style", ""))
        self.stroke_width = self._get_stroke_width()
        self.stroke_color = self._get_stroke_color()
        self.segments = self._parse_path_data()
        
    def _parse_style(self, style_str: str) -> Dict[str, str]:
        """Parse SVG style attribute.
        
        Args:
            style_str: Style attribute string
            
        Returns:
            Dictionary of style properties
        """
        if not style_str:
            return {}
            
        style_dict = {}
        for item in style_str.split(";"):
            if ":" in item:
                key, value = item.split(":", 1)
                style_dict[key.strip()] = value.strip()
                
        return style_dict
        
    def _get_stroke_width(self) -> float:
        """Get stroke width from element attributes or style.
        
        Returns:
            Stroke width as float
        """
        # Check direct attribute first
        width = self.element.get("stroke-width")
        
        # Then check style dictionary
        if not width and "stroke-width" in self.style:
            width = self.style["stroke-width"]
            
        # Parse value
        if width:
            try:
                return float(width.replace("px", ""))
            except ValueError:
                pass
                
        # Default value
        return 1.0
        
    def _get_stroke_color(self) -> str:
        """Get stroke color from element attributes or style.
        
        Returns:
            Stroke color as string
        """
        # Check direct attribute first
        color = self.element.get("stroke")
        
        # Then check style dictionary
        if not color and "stroke" in self.style:
            color = self.style["stroke"]
            
        # Default value
        return color or "#000000"
        
    def add_transform(self, transform_str: str):
        """Add a transform to the path's transform chain.
        
        Args:
            transform_str: SVG transform string
        """
        matrix = self._parse_transform(transform_str)
        if matrix is not None:
            # Multiply with existing transform (matrix multiplication)
            self.transform_matrix = np.dot(matrix, self.transform_matrix)
            
    def _parse_transform(self, transform_str: str) -> Optional[np.ndarray]:
        """Parse SVG transform attribute into transformation matrix.
        
        Args:
            transform_str: SVG transform string
            
        Returns:
            3x3 transformation matrix as numpy array
        """
        if not transform_str:
            return None
            
        # Initialize identity matrix
        matrix = np.identity(3)
        
        # Handle different transform types
        transform_str = transform_str.strip()
        
        if transform_str.startswith("matrix("):
            # Parse matrix transform: matrix(a,b,c,d,e,f)
            values_str = transform_str[7:-1]  # Remove "matrix(" and ")"
            values = [float(v.strip()) for v in values_str.split(",")]
            if len(values) == 6:
                # Convert to 3x3 matrix
                matrix = np.array([
                    [values[0], values[2], values[4]],
                    [values[1], values[3], values[5]],
                    [0, 0, 1]
                ])
                
        elif transform_str.startswith("translate("):
            # Parse translate transform: translate(x,y)
            values_str = transform_str[10:-1]  # Remove "translate(" and ")"
            values = [float(v.strip()) for v in values_str.split(",")]
            if len(values) >= 1:
                tx = values[0]
                ty = values[1] if len(values) > 1 else 0
                matrix = np.array([
                    [1, 0, tx],
                    [0, 1, ty],
                    [0, 0, 1]
                ])
                
        elif transform_str.startswith("scale("):
            # Parse scale transform: scale(x,y) or scale(s)
            values_str = transform_str[6:-1]  # Remove "scale(" and ")"
            values = [float(v.strip()) for v in values_str.split(",")]
            if len(values) >= 1:
                sx = values[0]
                sy = values[1] if len(values) > 1 else sx
                matrix = np.array([
                    [sx, 0, 0],
                    [0, sy, 0],
                    [0, 0, 1]
                ])
                
        elif transform_str.startswith("rotate("):
            # Parse rotate transform: rotate(angle,cx,cy) or rotate(angle)
            values_str = transform_str[7:-1]  # Remove "rotate(" and ")"
            values = [float(v.strip()) for v in values_str.split(",")]
            if len(values) >= 1:
                angle_deg = values[0]
                angle_rad = np.radians(angle_deg)
                cos_a = np.cos(angle_rad)
                sin_a = np.sin(angle_rad)
                
                if len(values) >= 3:
                    # Rotation around point (cx, cy)
                    cx, cy = values[1], values[2]
                    # Translate to origin, rotate, translate back
                    t1 = np.array([[1, 0, cx], [0, 1, cy], [0, 0, 1]])
                    r = np.array([[cos_a, -sin_a, 0], [sin_a, cos_a, 0], [0, 0, 1]])
                    t2 = np.array([[1, 0, -cx], [0, 1, -cy], [0, 0, 1]])
                    matrix = np.dot(np.dot(t1, r), t2)
                else:
                    # Rotation around origin
                    matrix = np.array([
                        [cos_a, -sin_a, 0],
                        [sin_a, cos_a, 0],
                        [0, 0, 1]
                    ])
        
        return matrix
        
    def _parse_path_data(self) -> List[Tuple]:
        """Parse SVG path data into segments.
        
        Returns:
            List of path segments
        """
        # For now, we'll just store the raw path data
        # In a future version, we'll parse this into line segments
        # For this initial implementation, we're focusing on the structure
        return [(self.path_data, self.stroke_width, self.stroke_color)]
        
    def transform_point(self, x: float, y: float) -> Tuple[float, float]:
        """Transform a point using the path's transformation matrix.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Transformed (x, y) coordinates
        """
        # Create homogeneous coordinates
        point = np.array([x, y, 1])
        
        # Apply transformation
        transformed = np.dot(self.transform_matrix, point)
        
        # Return as tuple
        return (transformed[0], transformed[1])


def parse_svg(file_path: Union[str, Path]) -> SVGDocument:
    """Parse an SVG file and return the document object.
    
    Args:
        file_path: Path to SVG file
        
    Returns:
        SVGDocument object
    """
    return SVGDocument(file_path) 