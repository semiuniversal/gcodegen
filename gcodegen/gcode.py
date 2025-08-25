"""G-code generation module for GCodeGen.

This module handles generating G-code commands for the H.Airbrush device.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Set up logging
logger = logging.getLogger(__name__)


class GCodeGenerator:
    """G-code generator for H.Airbrush device."""

    def __init__(self, config: Dict = None):
        """Initialize G-code generator.

        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or {}
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.current_tool = None
        self.current_feed_rate = None
        self.output_lines = []
        
    def comment(self, text: str) -> str:
        """Generate a comment.

        Args:
            text: Comment text

        Returns:
            G-code comment
        """
        return f"; {text}"
        
    def move_to(self, x: Optional[float] = None, y: Optional[float] = None, 
                z: Optional[float] = None, feed_rate: Optional[float] = None) -> str:
        """Generate a linear move command.

        Args:
            x: X coordinate (optional)
            y: Y coordinate (optional)
            z: Z coordinate (optional)
            feed_rate: Feed rate in mm/min (optional)

        Returns:
            G-code move command
        """
        # Start building the command
        command = "G1"
        
        # Add coordinates if provided
        if x is not None:
            command += f" X{x:.3f}"
            self.current_x = x
            
        if y is not None:
            command += f" Y{y:.3f}"
            self.current_y = y
            
        if z is not None:
            command += f" Z{z:.3f}"
            self.current_z = z
            
        # Add feed rate if provided
        if feed_rate is not None:
            command += f" F{feed_rate:.0f}"
            self.current_feed_rate = feed_rate
            
        return command
        
    def rapid_move_to(self, x: Optional[float] = None, y: Optional[float] = None, 
                      z: Optional[float] = None) -> str:
        """Generate a rapid move command.

        Args:
            x: X coordinate (optional)
            y: Y coordinate (optional)
            z: Z coordinate (optional)

        Returns:
            G-code rapid move command
        """
        # Start building the command
        command = "G0"
        
        # Add coordinates if provided
        if x is not None:
            command += f" X{x:.3f}"
            self.current_x = x
            
        if y is not None:
            command += f" Y{y:.3f}"
            self.current_y = y
            
        if z is not None:
            command += f" Z{z:.3f}"
            self.current_z = z
            
        return command
        
    def set_units(self, units: str = "mm") -> str:
        """Set units for G-code.

        Args:
            units: Units to use ("mm" or "in")

        Returns:
            G-code units command
        """
        if units.lower() == "mm":
            return "G21 ; Set units to millimeters"
        elif units.lower() == "in":
            return "G20 ; Set units to inches"
        else:
            logger.warning(f"Unknown units: {units}, defaulting to mm")
            return "G21 ; Set units to millimeters (default)"
            
    def set_absolute_positioning(self) -> str:
        """Set absolute positioning mode.

        Returns:
            G-code absolute positioning command
        """
        return "G90 ; Use absolute coordinates"
        
    def set_relative_positioning(self) -> str:
        """Set relative positioning mode.

        Returns:
            G-code relative positioning command
        """
        return "G91 ; Use relative coordinates"
        
    def set_tool(self, tool_number: int) -> str:
        """Set active tool.

        Args:
            tool_number: Tool number (0, 1, etc.)

        Returns:
            G-code tool selection command
        """
        self.current_tool = tool_number
        return f"T{tool_number} ; Select tool {tool_number}"
        
    def home_axes(self, x: bool = True, y: bool = True, z: bool = False) -> str:
        """Home specified axes.

        Args:
            x: Home X axis (default: True)
            y: Home Y axis (default: True)
            z: Home Z axis (default: False)

        Returns:
            G-code home command
        """
        command = "G28"
        
        if x:
            command += " X"
            self.current_x = 0
            
        if y:
            command += " Y"
            self.current_y = 0
            
        if z:
            command += " Z"
            self.current_z = 0
            
        return command + " ; Home axes"
        
    def disable_motors(self) -> str:
        """Disable stepper motors.

        Returns:
            G-code disable motors command
        """
        return "M84 ; Disable motors"
        
    def dwell(self, milliseconds: int) -> str:
        """Pause execution for specified time.

        Args:
            milliseconds: Time to pause in milliseconds

        Returns:
            G-code dwell command
        """
        return f"G4 P{milliseconds} ; Dwell for {milliseconds}ms"
        
    def set_fan_speed(self, speed: int, fan_number: int = 0) -> str:
        """Set fan speed.

        Args:
            speed: Fan speed (0-255)
            fan_number: Fan number (default: 0)

        Returns:
            G-code fan speed command
        """
        # Ensure speed is in range 0-255
        speed = max(0, min(255, speed))
        return f"M106 P{fan_number} S{speed} ; Set fan {fan_number} speed to {speed}"
        
    def turn_fan_off(self, fan_number: int = 0) -> str:
        """Turn fan off.

        Args:
            fan_number: Fan number (default: 0)

        Returns:
            G-code fan off command
        """
        return f"M107 P{fan_number} ; Turn fan {fan_number} off"
        
    def set_extrusion_rate(self, rate: float) -> str:
        """Set extrusion rate.

        Args:
            rate: Extrusion rate multiplier

        Returns:
            G-code extrusion rate command
        """
        return f"M221 S{rate:.2f} ; Set flow rate factor"
        
    def add_line(self, line: str) -> None:
        """Add a line to the output.

        Args:
            line: G-code line to add
        """
        self.output_lines.append(line)
        
    def add_lines(self, lines: List[str]) -> None:
        """Add multiple lines to the output.

        Args:
            lines: G-code lines to add
        """
        self.output_lines.extend(lines)
        
    def generate_start_commands(self) -> List[str]:
        """Generate start commands.

        Returns:
            List of G-code start commands
        """
        # Get start commands from config or use defaults
        start_commands = self.config.get("gcode", {}).get("start_commands", [
            "G21 ; Set units to millimeters",
            "G90 ; Use absolute coordinates",
            "M83 ; Use relative distances for extrusion",
        ])
        
        return start_commands
        
    def generate_end_commands(self) -> List[str]:
        """Generate end commands.

        Returns:
            List of G-code end commands
        """
        # Get end commands from config or use defaults
        end_commands = self.config.get("gcode", {}).get("end_commands", [
            "G1 Z10 F1000 ; Raise Z",
            "G28 X Y ; Home X and Y",
            "M84 ; Disable motors",
        ])
        
        return end_commands
        
    def generate_tool_change_commands(self, tool_number: int) -> List[str]:
        """Generate tool change commands.

        Args:
            tool_number: Tool number (0, 1, etc.)

        Returns:
            List of G-code tool change commands
        """
        # Get tool change commands from config or use defaults
        tool_key = f"tool{tool_number}"
        tool_change_commands = self.config.get("gcode", {}).get("tool_change_commands", {}).get(
            tool_key, [f"T{tool_number} ; Select tool {tool_number}"]
        )
        
        return tool_change_commands
        
    def generate_safe_travel_move(self, x: float, y: float) -> List[str]:
        """Generate a safe travel move.

        Args:
            x: Target X coordinate
            y: Target Y coordinate

        Returns:
            List of G-code commands for safe travel
        """
        commands = []
        
        # Get safe Z height from config or use default
        safe_z = self.config.get("machine", {}).get("safe_z", 5)
        
        # Get travel speed from config or use default
        travel_speed = self.config.get("machine", {}).get("travel_speed", 3000)
        
        # Raise Z to safe height if needed
        if self.current_z < safe_z:
            commands.append(self.move_to(z=safe_z, feed_rate=travel_speed))
            
        # Move to target XY position
        commands.append(self.move_to(x=x, y=y, feed_rate=travel_speed))
        
        return commands
        
    def generate_work_move(self, x: float, y: float, z: Optional[float] = None) -> str:
        """Generate a work move.

        Args:
            x: Target X coordinate
            y: Target Y coordinate
            z: Target Z coordinate (optional)

        Returns:
            G-code work move command
        """
        # Get work speed from config or use default
        work_speed = self.config.get("machine", {}).get("work_speed", 1500)
        
        # Move to target position
        return self.move_to(x=x, y=y, z=z, feed_rate=work_speed)
        
    def save_to_file(self, file_path: Union[str, Path]) -> bool:
        """Save G-code to file.

        Args:
            file_path: Path to output file

        Returns:
            True if file was saved successfully, False otherwise
        """
        try:
            with open(file_path, "w") as f:
                for line in self.output_lines:
                    f.write(line + "\n")
                    
            logger.info(f"G-code saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving G-code to {file_path}: {e}")
            return False
            
    def get_output(self) -> str:
        """Get G-code output as a string.

        Returns:
            G-code output
        """
        return "\n".join(self.output_lines)
        
    def clear_output(self) -> None:
        """Clear G-code output."""
        self.output_lines = []


def generate_gcode(paths: List[Tuple], config: Dict) -> str:
    """Generate G-code from paths.

    Args:
        paths: List of path tuples (path_data, stroke_width, stroke_color)
        config: Configuration dictionary

    Returns:
        G-code output
    """
    generator = GCodeGenerator(config)
    
    # Add start commands
    generator.add_lines(generator.generate_start_commands())
    generator.add_line(generator.comment("Generated by GCodeGen"))
    
    # TODO: Implement path to G-code conversion
    # This will be implemented in a future version
    
    # Add end commands
    generator.add_lines(generator.generate_end_commands())
    
    return generator.get_output() 