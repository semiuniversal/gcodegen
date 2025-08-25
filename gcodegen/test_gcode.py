#!/usr/bin/env python3
"""Test script for the G-code generation module.

This script tests the G-code generation module's functionality.
"""

import argparse
import logging
import sys
import tempfile
from pathlib import Path

from gcodegen.gcode import GCodeGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("test_gcode")


def test_basic_commands():
    """Test basic G-code commands."""
    logger.info("Testing basic G-code commands...")
    
    # Create G-code generator
    generator = GCodeGenerator()
    
    # Test comments
    comment = generator.comment("Test comment")
    logger.info(f"Comment: {comment}")
    assert comment == "; Test comment"
    
    # Test move commands
    move = generator.move_to(x=10, y=20, z=5, feed_rate=1000)
    logger.info(f"Move: {move}")
    assert move == "G1 X10.000 Y20.000 Z5.000 F1000"
    assert generator.current_x == 10
    assert generator.current_y == 20
    assert generator.current_z == 5
    assert generator.current_feed_rate == 1000
    
    # Test rapid move commands
    rapid_move = generator.rapid_move_to(x=30, y=40, z=10)
    logger.info(f"Rapid move: {rapid_move}")
    assert rapid_move == "G0 X30.000 Y40.000 Z10.000"
    assert generator.current_x == 30
    assert generator.current_y == 40
    assert generator.current_z == 10
    
    # Test units commands
    mm_units = generator.set_units("mm")
    logger.info(f"Set units to mm: {mm_units}")
    assert mm_units == "G21 ; Set units to millimeters"
    
    inch_units = generator.set_units("in")
    logger.info(f"Set units to inches: {inch_units}")
    assert inch_units == "G20 ; Set units to inches"
    
    # Test positioning commands
    abs_pos = generator.set_absolute_positioning()
    logger.info(f"Set absolute positioning: {abs_pos}")
    assert abs_pos == "G90 ; Use absolute coordinates"
    
    rel_pos = generator.set_relative_positioning()
    logger.info(f"Set relative positioning: {rel_pos}")
    assert rel_pos == "G91 ; Use relative coordinates"
    
    # Test tool commands
    tool = generator.set_tool(1)
    logger.info(f"Set tool: {tool}")
    assert tool == "T1 ; Select tool 1"
    assert generator.current_tool == 1
    
    return True


def test_complex_commands():
    """Test more complex G-code commands."""
    logger.info("Testing complex G-code commands...")
    
    # Create G-code generator
    generator = GCodeGenerator()
    
    # Test home axes command
    home_xy = generator.home_axes(x=True, y=True, z=False)
    logger.info(f"Home X and Y: {home_xy}")
    assert home_xy == "G28 X Y ; Home axes"
    assert generator.current_x == 0
    assert generator.current_y == 0
    
    # Test disable motors command
    disable = generator.disable_motors()
    logger.info(f"Disable motors: {disable}")
    assert disable == "M84 ; Disable motors"
    
    # Test dwell command
    dwell = generator.dwell(1000)
    logger.info(f"Dwell: {dwell}")
    assert dwell == "G4 P1000 ; Dwell for 1000ms"
    
    # Test fan commands
    fan_on = generator.set_fan_speed(255)
    logger.info(f"Fan on: {fan_on}")
    assert fan_on == "M106 P0 S255 ; Set fan 0 speed to 255"
    
    fan_off = generator.turn_fan_off()
    logger.info(f"Fan off: {fan_off}")
    assert fan_off == "M107 P0 ; Turn fan 0 off"
    
    # Test extrusion rate command
    extrusion = generator.set_extrusion_rate(1.5)
    logger.info(f"Set extrusion rate: {extrusion}")
    assert extrusion == "M221 S1.50 ; Set flow rate factor"
    
    return True


def test_output_generation():
    """Test G-code output generation."""
    logger.info("Testing G-code output generation...")
    
    # Create G-code generator
    generator = GCodeGenerator()
    
    # Add some commands
    generator.add_line(generator.comment("Start of G-code"))
    generator.add_line(generator.set_units("mm"))
    generator.add_line(generator.set_absolute_positioning())
    generator.add_line(generator.home_axes(x=True, y=True, z=True))
    generator.add_line(generator.move_to(x=10, y=10, z=5, feed_rate=3000))
    generator.add_line(generator.set_tool(0))
    generator.add_line(generator.move_to(z=0, feed_rate=1000))
    generator.add_line(generator.move_to(x=20, y=20, feed_rate=1500))
    generator.add_line(generator.move_to(x=30, y=10, feed_rate=1500))
    generator.add_line(generator.move_to(x=10, y=10, feed_rate=1500))
    generator.add_line(generator.move_to(z=5, feed_rate=1000))
    generator.add_line(generator.home_axes(x=True, y=True, z=False))
    generator.add_line(generator.disable_motors())
    generator.add_line(generator.comment("End of G-code"))
    
    # Get output
    output = generator.get_output()
    logger.info(f"G-code output:\n{output}")
    
    # Check output lines
    lines = output.split("\n")
    assert len(lines) == 14
    assert lines[0] == "; Start of G-code"
    assert lines[-1] == "; End of G-code"
    
    # Test saving to file
    with tempfile.NamedTemporaryFile(suffix=".gcode", delete=False) as temp_file:
        temp_path = Path(temp_file.name)
        
    try:
        # Save to file
        result = generator.save_to_file(temp_path)
        assert result
        logger.info(f"Saved G-code to {temp_path}")
        
        # Read file back
        with open(temp_path, "r") as f:
            file_content = f.read()
            
        # Check file content
        assert file_content == output + "\n"
        
        # Test clear output
        generator.clear_output()
        assert generator.get_output() == ""
        assert len(generator.output_lines) == 0
        
        return True
        
    finally:
        # Clean up the temporary file
        temp_path.unlink(missing_ok=True)


def test_config_integration():
    """Test integration with configuration."""
    logger.info("Testing configuration integration...")
    
    # Create a custom configuration
    config = {
        "machine": {
            "safe_z": 10,
            "travel_speed": 5000,
            "work_speed": 2000,
        },
        "gcode": {
            "start_commands": [
                "G21 ; Custom units",
                "G90 ; Custom coordinates",
            ],
            "end_commands": [
                "G1 Z20 F1000 ; Custom Z raise",
                "M84 ; Custom disable motors",
            ],
            "tool_change_commands": {
                "tool0": ["T0 ; Custom tool 0", "M400 ; Wait for moves to complete"],
            },
        },
    }
    
    # Create G-code generator with config
    generator = GCodeGenerator(config)
    
    # Test start commands
    start_commands = generator.generate_start_commands()
    logger.info(f"Start commands: {start_commands}")
    assert len(start_commands) == 2
    assert start_commands[0] == "G21 ; Custom units"
    
    # Test end commands
    end_commands = generator.generate_end_commands()
    logger.info(f"End commands: {end_commands}")
    assert len(end_commands) == 2
    assert end_commands[0] == "G1 Z20 F1000 ; Custom Z raise"
    
    # Test tool change commands
    tool_commands = generator.generate_tool_change_commands(0)
    logger.info(f"Tool change commands: {tool_commands}")
    assert len(tool_commands) == 2
    assert tool_commands[0] == "T0 ; Custom tool 0"
    
    # Test safe travel move
    generator.current_z = 0  # Set current Z to 0
    travel_commands = generator.generate_safe_travel_move(50, 60)
    logger.info(f"Safe travel commands: {travel_commands}")
    assert len(travel_commands) == 2
    assert "Z10.000" in travel_commands[0]
    assert "F5000" in travel_commands[0]
    assert "X50.000 Y60.000" in travel_commands[1]
    
    # Test work move
    work_move = generator.generate_work_move(70, 80)
    logger.info(f"Work move: {work_move}")
    assert "X70.000 Y80.000" in work_move
    assert "F2000" in work_move
    
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test G-code generation module")
    args = parser.parse_args()
    
    success_count = 0
    failure_count = 0
    
    # Test basic commands
    if test_basic_commands():
        success_count += 1
    else:
        failure_count += 1
        
    # Test complex commands
    if test_complex_commands():
        success_count += 1
    else:
        failure_count += 1
        
    # Test output generation
    if test_output_generation():
        success_count += 1
    else:
        failure_count += 1
        
    # Test config integration
    if test_config_integration():
        success_count += 1
    else:
        failure_count += 1
        
    logger.info(f"Test results: {success_count} succeeded, {failure_count} failed")


if __name__ == "__main__":
    main() 