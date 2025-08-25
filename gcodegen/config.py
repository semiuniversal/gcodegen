"""Configuration module for GCodeGen.

This module handles loading and validating configuration from YAML files.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

# Set up logging
logger = logging.getLogger(__name__)


class Config:
    """Configuration handler for GCodeGen."""

    # Default configuration values
    DEFAULT_CONFIG = {
        "machine": {
            "name": "H.Airbrush",
            "bed_size_x": 400,  # mm
            "bed_size_y": 400,  # mm
            "head_offsets": {
                "tool0": {"x": 0, "y": 0},  # mm
                "tool1": {"x": 0, "y": 0},  # mm
            },
            "safe_z": 5,  # mm
            "travel_speed": 3000,  # mm/min
            "work_speed": 1500,  # mm/min
        },
        "gcode": {
            "start_commands": [
                "G21 ; Set units to millimeters",
                "G90 ; Use absolute coordinates",
                "M83 ; Use relative distances for extrusion",
            ],
            "end_commands": [
                "G1 Z10 F1000 ; Raise Z",
                "G28 X Y ; Home X and Y",
                "M84 ; Disable motors",
            ],
            "tool_change_commands": {
                "tool0": ["T0 ; Select tool 0"],
                "tool1": ["T1 ; Select tool 1"],
            },
        },
        "svg": {
            "default_units": "mm",  # mm, in, px
            "dpi": 96,  # For px to mm conversion
            "invert_y": True,  # Invert Y coordinates (SVG has Y=0 at top)
            "origin": "bottom-left",  # bottom-left, center, top-left
        },
        "tools": {
            "tool0": {
                "name": "Black",
                "color": "#000000",
                "min_width": 0.3,  # mm
                "max_width": 2.0,  # mm
                "width_to_flow_factor": 1.0,  # Flow multiplier based on width
            },
            "tool1": {
                "name": "White",
                "color": "#FFFFFF",
                "min_width": 0.3,  # mm
                "max_width": 2.0,  # mm
                "width_to_flow_factor": 1.0,  # Flow multiplier based on width
            },
        },
    }

    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """Initialize configuration.

        Args:
            config_file: Path to YAML configuration file (optional)
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_file:
            self.load_config(config_file)
            
    def load_config(self, config_file: Union[str, Path]) -> bool:
        """Load configuration from YAML file.

        Args:
            config_file: Path to YAML configuration file

        Returns:
            True if config was loaded successfully, False otherwise
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return False
            
        try:
            with open(config_path, "r") as f:
                user_config = yaml.safe_load(f)
                
            if not user_config:
                logger.warning(f"Empty configuration file: {config_path}")
                return False
                
            # Merge user config with default config
            self._merge_config(self.config, user_config)
            logger.info(f"Loaded configuration from {config_path}")
            return True
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
            
    def _merge_config(self, target: Dict, source: Dict) -> None:
        """Recursively merge source dict into target dict.

        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                self._merge_config(target[key], value)
            else:
                # Replace or add values
                target[key] = value
                
    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation path.

        Args:
            path: Configuration path (e.g., "machine.bed_size_x")
            default: Default value if path not found

        Returns:
            Configuration value or default
        """
        parts = path.split(".")
        value = self.config
        
        try:
            for part in parts:
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, path: str, value: Any) -> None:
        """Set configuration value using dot notation path.

        Args:
            path: Configuration path (e.g., "machine.bed_size_x")
            value: Value to set
        """
        parts = path.split(".")
        config = self.config
        
        # Navigate to the parent of the target
        for part in parts[:-1]:
            if part not in config or not isinstance(config[part], dict):
                config[part] = {}
            config = config[part]
            
        # Set the value
        config[parts[-1]] = value
        
    def save(self, config_file: Union[str, Path]) -> bool:
        """Save configuration to YAML file.

        Args:
            config_file: Path to YAML configuration file

        Returns:
            True if config was saved successfully, False otherwise
        """
        config_path = Path(config_file)
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(config_path.parent, exist_ok=True)
            
            with open(config_path, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
                
            logger.info(f"Saved configuration to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
            
    def validate(self) -> bool:
        """Validate configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        # TODO: Implement more thorough validation
        
        # Check required sections
        required_sections = ["machine", "gcode", "svg", "tools"]
        for section in required_sections:
            if section not in self.config:
                logger.error(f"Missing required configuration section: {section}")
                return False
                
        # Check machine settings
        machine = self.config.get("machine", {})
        if not machine.get("bed_size_x") or not machine.get("bed_size_y"):
            logger.error("Machine bed size not specified")
            return False
            
        # Check tool settings
        tools = self.config.get("tools", {})
        if not tools:
            logger.error("No tools configured")
            return False
            
        return True


def load_config(config_file: Optional[Union[str, Path]] = None) -> Config:
    """Load configuration from file.

    Args:
        config_file: Path to YAML configuration file (optional)

    Returns:
        Config object
    """
    return Config(config_file) 