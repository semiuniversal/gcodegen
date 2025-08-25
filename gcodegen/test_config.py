#!/usr/bin/env python3
"""Test script for the configuration module.

This script tests the configuration module's functionality.
"""

import argparse
import logging
import sys
import tempfile
from pathlib import Path

from gcodegen.config import Config, load_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("test_config")


def test_default_config():
    """Test loading default configuration."""
    logger.info("Testing default configuration...")
    
    # Load default configuration
    config = Config()
    
    # Check some default values
    machine_name = config.get("machine.name")
    logger.info(f"Machine name: {machine_name}")
    
    bed_size_x = config.get("machine.bed_size_x")
    bed_size_y = config.get("machine.bed_size_y")
    logger.info(f"Bed size: {bed_size_x} x {bed_size_y} mm")
    
    # Check a nested value
    tool0_offset_x = config.get("machine.head_offsets.tool0.x")
    tool0_offset_y = config.get("machine.head_offsets.tool0.y")
    logger.info(f"Tool 0 offset: ({tool0_offset_x}, {tool0_offset_y})")
    
    # Check a non-existent value
    non_existent = config.get("non.existent.path", "default_value")
    logger.info(f"Non-existent value: {non_existent}")
    
    return True


def test_custom_config():
    """Test loading and saving custom configuration."""
    logger.info("Testing custom configuration...")
    
    # Create a temporary file for the configuration
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        temp_path = Path(temp_file.name)
    
    try:
        # Create a custom configuration
        custom_config = {
            "machine": {
                "name": "Custom Machine",
                "bed_size_x": 500,
                "bed_size_y": 600,
            },
            "tools": {
                "tool0": {
                    "name": "Custom Black",
                    "color": "#111111",
                }
            }
        }
        
        # Create a config object and update it
        config = Config()
        for key, value in custom_config.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, dict):
                        for subsubkey, subsubvalue in subvalue.items():
                            config.set(f"{key}.{subkey}.{subsubkey}", subsubvalue)
                    else:
                        config.set(f"{key}.{subkey}", subvalue)
            else:
                config.set(key, value)
        
        # Save the configuration
        if not config.save(temp_path):
            logger.error("Failed to save configuration")
            return False
            
        # Load the configuration
        new_config = Config(temp_path)
        
        # Check the custom values
        machine_name = new_config.get("machine.name")
        logger.info(f"Custom machine name: {machine_name}")
        assert machine_name == "Custom Machine"
        
        bed_size_x = new_config.get("machine.bed_size_x")
        bed_size_y = new_config.get("machine.bed_size_y")
        logger.info(f"Custom bed size: {bed_size_x} x {bed_size_y} mm")
        assert bed_size_x == 500
        assert bed_size_y == 600
        
        tool_name = new_config.get("tools.tool0.name")
        tool_color = new_config.get("tools.tool0.color")
        logger.info(f"Custom tool: {tool_name} ({tool_color})")
        assert tool_name == "Custom Black"
        assert tool_color == "#111111"
        
        # Check that default values are preserved
        travel_speed = new_config.get("machine.travel_speed")
        logger.info(f"Default travel speed (preserved): {travel_speed}")
        assert travel_speed == 3000
        
        return True
        
    finally:
        # Clean up the temporary file
        temp_path.unlink(missing_ok=True)


def test_validation():
    """Test configuration validation."""
    logger.info("Testing configuration validation...")
    
    # Create a valid configuration
    config = Config()
    assert config.validate()
    logger.info("Default configuration is valid")
    
    # Create an invalid configuration (missing tools)
    invalid_config = Config()
    invalid_config.config.pop("tools")
    assert not invalid_config.validate()
    logger.info("Invalid configuration (missing tools) failed validation")
    
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test configuration module")
    args = parser.parse_args()
    
    success_count = 0
    failure_count = 0
    
    # Test default configuration
    if test_default_config():
        success_count += 1
    else:
        failure_count += 1
        
    # Test custom configuration
    if test_custom_config():
        success_count += 1
    else:
        failure_count += 1
        
    # Test validation
    if test_validation():
        success_count += 1
    else:
        failure_count += 1
        
    logger.info(f"Test results: {success_count} succeeded, {failure_count} failed")


if __name__ == "__main__":
    main() 