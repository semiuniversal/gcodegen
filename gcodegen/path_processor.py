"""
Path processing utilities for SVG path data.

This module provides functionality for parsing SVG path data and converting
paths to polylines for G-code generation. It replaces the inkex path processing
functionality with a standalone implementation.
"""

import re
import math
from typing import List, Tuple, Dict, Any, Optional, Union


class PathCommand:
    """Represents a single SVG path command."""
    
    def __init__(self, command: str, params: List[float]):
        """
        Initialize a path command.
        
        Args:
            command (str): The SVG path command letter (M, L, C, etc.)
            params (List[float]): The parameters for the command
        """
        self.command = command
        self.params = params
        self.absolute = command.isupper()
        
    def __repr__(self) -> str:
        return f"{self.command}{self.params}"


class PathProcessor:
    """Processes SVG path data into polylines for G-code generation."""
    
    @staticmethod
    def parse_path(path_data: str) -> List[PathCommand]:
        """
        Parse SVG path data into a list of PathCommand objects.
        
        Args:
            path_data (str): SVG path data string
            
        Returns:
            List[PathCommand]: List of parsed path commands
        """
        if not path_data:
            return []
            
        # Regular expression to match path commands and parameters
        command_regex = r"([MLHVCSQTAZmlhvcsqtaz])([^MLHVCSQTAZmlhvcsqtaz]*)"
        
        # Find all commands and their parameters
        commands = []
        for match in re.finditer(command_regex, path_data):
            cmd = match.group(1)
            params_str = match.group(2).strip()
            
            # Parse parameters
            params = []
            if params_str:
                # Split by either commas or spaces
                params_parts = re.split(r"[\s,]+", params_str)
                # Convert to float
                params = [float(p) for p in params_parts if p]
            
            commands.append(PathCommand(cmd, params))
            
        return commands
    
    @staticmethod
    def path_to_polyline(path_commands: List[PathCommand], curve_resolution: int = 20) -> List[Tuple[float, float]]:
        """
        Convert a list of path commands to a polyline (list of points).
        
        Args:
            path_commands (List[PathCommand]): List of path commands
            curve_resolution (int): Number of segments to use for curves
            
        Returns:
            List[Tuple[float, float]]: List of (x, y) points
        """
        if not path_commands:
            return []
            
        polyline = []
        current_x, current_y = 0.0, 0.0
        subpath_start_x, subpath_start_y = 0.0, 0.0
        
        for cmd in path_commands:
            command = cmd.command
            params = cmd.params
            
            # Handle different command types
            if command in 'Mm':
                # Move command
                if command == 'M':  # Absolute
                    for i in range(0, len(params), 2):
                        if i == 0:
                            current_x, current_y = params[i], params[i+1]
                            subpath_start_x, subpath_start_y = current_x, current_y
                        else:
                            # Subsequent points are treated as implicit line commands
                            current_x, current_y = params[i], params[i+1]
                        polyline.append((current_x, current_y))
                else:  # Relative
                    for i in range(0, len(params), 2):
                        if i == 0:
                            current_x += params[i]
                            current_y += params[i+1]
                            subpath_start_x, subpath_start_y = current_x, current_y
                        else:
                            # Subsequent points are treated as implicit line commands
                            current_x += params[i]
                            current_y += params[i+1]
                        polyline.append((current_x, current_y))
                        
            elif command in 'Ll':
                # Line command
                if command == 'L':  # Absolute
                    for i in range(0, len(params), 2):
                        current_x, current_y = params[i], params[i+1]
                        polyline.append((current_x, current_y))
                else:  # Relative
                    for i in range(0, len(params), 2):
                        current_x += params[i]
                        current_y += params[i+1]
                        polyline.append((current_x, current_y))
                        
            elif command in 'Hh':
                # Horizontal line command
                if command == 'H':  # Absolute
                    for x in params:
                        current_x = x
                        polyline.append((current_x, current_y))
                else:  # Relative
                    for x in params:
                        current_x += x
                        polyline.append((current_x, current_y))
                        
            elif command in 'Vv':
                # Vertical line command
                if command == 'V':  # Absolute
                    for y in params:
                        current_y = y
                        polyline.append((current_x, current_y))
                else:  # Relative
                    for y in params:
                        current_y += y
                        polyline.append((current_x, current_y))
                        
            elif command in 'Cc':
                # Cubic Bézier curve command
                if command == 'C':  # Absolute
                    for i in range(0, len(params), 6):
                        x1, y1 = params[i], params[i+1]
                        x2, y2 = params[i+2], params[i+3]
                        x, y = params[i+4], params[i+5]
                        
                        # Convert cubic Bézier to polyline
                        points = PathProcessor._cubic_bezier_to_polyline(
                            current_x, current_y, x1, y1, x2, y2, x, y, curve_resolution
                        )
                        polyline.extend(points)
                        
                        current_x, current_y = x, y
                else:  # Relative
                    for i in range(0, len(params), 6):
                        x1, y1 = current_x + params[i], current_y + params[i+1]
                        x2, y2 = current_x + params[i+2], current_y + params[i+3]
                        x, y = current_x + params[i+4], current_y + params[i+5]
                        
                        # Convert cubic Bézier to polyline
                        points = PathProcessor._cubic_bezier_to_polyline(
                            current_x, current_y, x1, y1, x2, y2, x, y, curve_resolution
                        )
                        polyline.extend(points)
                        
                        current_x, current_y = x, y
                        
            elif command in 'Ss':
                # Smooth cubic Bézier curve command
                # First control point is reflection of previous control point
                if len(polyline) < 1:
                    # If no previous command, treat as a regular cubic Bézier
                    # with the first control point coincident with the current point
                    prev_x2, prev_y2 = current_x, current_y
                else:
                    # Reflect the previous control point
                    prev_x2, prev_y2 = current_x, current_y  # Default if no previous control point
                
                if command == 'S':  # Absolute
                    for i in range(0, len(params), 4):
                        x2, y2 = params[i], params[i+1]
                        x, y = params[i+2], params[i+3]
                        
                        # First control point is reflection of previous second control point
                        x1 = 2 * current_x - prev_x2
                        y1 = 2 * current_y - prev_y2
                        
                        # Convert cubic Bézier to polyline
                        points = PathProcessor._cubic_bezier_to_polyline(
                            current_x, current_y, x1, y1, x2, y2, x, y, curve_resolution
                        )
                        polyline.extend(points)
                        
                        prev_x2, prev_y2 = x2, y2
                        current_x, current_y = x, y
                else:  # Relative
                    for i in range(0, len(params), 4):
                        x2, y2 = current_x + params[i], current_y + params[i+1]
                        x, y = current_x + params[i+2], current_y + params[i+3]
                        
                        # First control point is reflection of previous second control point
                        x1 = 2 * current_x - prev_x2
                        y1 = 2 * current_y - prev_y2
                        
                        # Convert cubic Bézier to polyline
                        points = PathProcessor._cubic_bezier_to_polyline(
                            current_x, current_y, x1, y1, x2, y2, x, y, curve_resolution
                        )
                        polyline.extend(points)
                        
                        prev_x2, prev_y2 = x2, y2
                        current_x, current_y = x, y
                        
            elif command in 'Zz':
                # Close path command - draw line back to subpath start
                if subpath_start_x != current_x or subpath_start_y != current_y:
                    polyline.append((subpath_start_x, subpath_start_y))
                current_x, current_y = subpath_start_x, subpath_start_y
                
            # Note: We're skipping Q, T, and A commands for now as they're less common
            # These can be added later if needed
                
        return polyline
    
    @staticmethod
    def _cubic_bezier_to_polyline(
        x0: float, y0: float,
        x1: float, y1: float,
        x2: float, y2: float,
        x3: float, y3: float,
        segments: int
    ) -> List[Tuple[float, float]]:
        """
        Convert a cubic Bézier curve to a polyline.
        
        Args:
            x0, y0: Start point
            x1, y1: First control point
            x2, y2: Second control point
            x3, y3: End point
            segments: Number of line segments to use
            
        Returns:
            List[Tuple[float, float]]: List of points along the curve
        """
        points = []
        
        for i in range(1, segments + 1):
            t = i / segments
            
            # Cubic Bézier formula
            # B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
            
            t_inv = 1 - t
            t_inv_squared = t_inv * t_inv
            t_inv_cubed = t_inv_squared * t_inv
            t_squared = t * t
            t_cubed = t_squared * t
            
            x = t_inv_cubed * x0 + 3 * t_inv_squared * t * x1 + 3 * t_inv * t_squared * x2 + t_cubed * x3
            y = t_inv_cubed * y0 + 3 * t_inv_squared * t * y1 + 3 * t_inv * t_squared * y2 + t_cubed * y3
            
            points.append((x, y))
            
        return points
    
    @staticmethod
    def _quadratic_bezier_to_polyline(
        x0: float, y0: float,
        x1: float, y1: float,
        x2: float, y2: float,
        segments: int
    ) -> List[Tuple[float, float]]:
        """
        Convert a quadratic Bézier curve to a polyline.
        
        Args:
            x0, y0: Start point
            x1, y1: Control point
            x2, y2: End point
            segments: Number of line segments to use
            
        Returns:
            List[Tuple[float, float]]: List of points along the curve
        """
        points = []
        
        for i in range(1, segments + 1):
            t = i / segments
            
            # Quadratic Bézier formula
            # B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
            
            t_inv = 1 - t
            t_inv_squared = t_inv * t_inv
            t_squared = t * t
            
            x = t_inv_squared * x0 + 2 * t_inv * t * x1 + t_squared * x2
            y = t_inv_squared * y0 + 2 * t_inv * t * y1 + t_squared * y2
            
            points.append((x, y))
            
        return points
    
    @staticmethod
    def _arc_to_polyline(
        x0: float, y0: float,
        rx: float, ry: float,
        x_axis_rotation: float,
        large_arc_flag: bool,
        sweep_flag: bool,
        x: float, y: float,
        segments: int
    ) -> List[Tuple[float, float]]:
        """
        Convert an SVG arc to a polyline.
        
        This is a simplified implementation that doesn't handle all cases correctly.
        For a complete implementation, refer to the SVG specification.
        
        Args:
            x0, y0: Start point
            rx, ry: Radii of the ellipse
            x_axis_rotation: Rotation of the ellipse in degrees
            large_arc_flag: Use the large arc (> 180 degrees)
            sweep_flag: Sweep direction (clockwise if True)
            x, y: End point
            segments: Number of line segments to use
            
        Returns:
            List[Tuple[float, float]]: List of points along the arc
        """
        # Convert to radians
        x_axis_rotation_rad = math.radians(x_axis_rotation)
        
        # Ensure rx and ry are positive
        rx, ry = abs(rx), abs(ry)
        
        # If rx or ry is 0, treat as a straight line
        if rx == 0 or ry == 0:
            return [(x, y)]
            
        # Step 1: Transform to origin
        dx = (x0 - x) / 2
        dy = (y0 - y) / 2
        
        # Step 2: Rotate to align with coordinate axes
        cos_phi = math.cos(x_axis_rotation_rad)
        sin_phi = math.sin(x_axis_rotation_rad)
        
        x1 = cos_phi * dx + sin_phi * dy
        y1 = -sin_phi * dx + cos_phi * dy
        
        # Step 3: Ensure radii are large enough
        lambda_value = (x1**2) / (rx**2) + (y1**2) / (ry**2)
        if lambda_value > 1:
            rx *= math.sqrt(lambda_value)
            ry *= math.sqrt(lambda_value)
        
        # Step 4: Compute center
        sign = -1 if large_arc_flag == sweep_flag else 1
        sq = max(0, (rx**2 * ry**2 - rx**2 * y1**2 - ry**2 * x1**2) / (rx**2 * y1**2 + ry**2 * x1**2))
        coef = sign * math.sqrt(sq)
        
        cx1 = coef * rx * y1 / ry
        cy1 = -coef * ry * x1 / rx
        
        # Step 5: Transform center back
        cx = cos_phi * cx1 - sin_phi * cy1 + (x0 + x) / 2
        cy = sin_phi * cx1 + cos_phi * cy1 + (y0 + y) / 2
        
        # Step 6: Compute start and sweep angles
        ux = (x1 - cx1) / rx
        uy = (y1 - cy1) / ry
        vx = (-x1 - cx1) / rx
        vy = (-y1 - cy1) / ry
        
        # Start angle
        start_angle = math.atan2(uy, ux)
        
        # Sweep angle
        n = math.sqrt(ux**2 + uy**2) * math.sqrt(vx**2 + vy**2)
        p = ux * vx + uy * vy
        d = p / n
        
        # Clamp d to [-1, 1] to handle floating point errors
        d = max(-1, min(d, 1))
        
        sweep_angle = math.acos(d)
        if ux * vy - uy * vx < 0:
            sweep_angle = -sweep_angle
            
        if not sweep_flag and sweep_angle > 0:
            sweep_angle -= 2 * math.pi
        elif sweep_flag and sweep_angle < 0:
            sweep_angle += 2 * math.pi
            
        # Step 7: Generate points along the arc
        points = []
        for i in range(1, segments + 1):
            t = i / segments
            angle = start_angle + t * sweep_angle
            
            # Compute point on ellipse
            ellipse_x = rx * math.cos(angle)
            ellipse_y = ry * math.sin(angle)
            
            # Rotate and translate back
            point_x = cos_phi * ellipse_x - sin_phi * ellipse_y + cx
            point_y = sin_phi * ellipse_x + cos_phi * ellipse_y + cy
            
            points.append((point_x, point_y))
            
        return points 