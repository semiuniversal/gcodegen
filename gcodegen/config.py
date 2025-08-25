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

# Default configuration file path
DEFAULT_CONFIG_FILE = Path(__file__).parent / "default_config.yaml"


def load_default_config() -> Dict:
    """Load default configuration from default_config.yaml.

    Returns:
        Default configuration dictionary
    """
    try:
        with open(DEFAULT_CONFIG_FILE, "r") as f:
            config = yaml.safe_load(f)
        return config or {}
    except Exception as e:
        logger.error(f"Error loading default configuration: {e}")
        return {}


def load_config(config_file: Optional[Union[str, Path]] = None) -> Dict:
    """Load configuration from YAML file.

    Args:
        config_file: Path to YAML configuration file (optional)

    Returns:
        Configuration dictionary
    """
    # Start with default configuration
    config = load_default_config()

    # If no config file specified, return default config
    if not config_file:
        return config

    # Load user configuration
    try:
        config_path = Path(config_file)
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return config

        with open(config_path, "r") as f:
            user_config = yaml.safe_load(f)

        if not user_config:
            logger.warning(f"Empty configuration file: {config_path}")
            return config

        # Merge user config with default config
        merge_config(config, user_config)
        logger.info(f"Loaded configuration from {config_path}")

    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {e}")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")

    return config


def merge_config(target: Dict, source: Dict) -> None:
    """Recursively merge source dict into target dict.

    Args:
        target: Target dictionary to merge into
        source: Source dictionary to merge from
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            merge_config(target[key], value)
        else:
            # Replace or add values
            target[key] = value


def get_config_value(config: Dict, path: str, default: Any = None) -> Any:
    """Get configuration value using dot notation path.

    Args:
        config: Configuration dictionary
        path: Configuration path (e.g., "machine.bed_size_x")
        default: Default value if path not found

    Returns:
        Configuration value or default
    """
    parts = path.split(".")
    value = config

    try:
        for part in parts:
            value = value[part]
        return value
    except (KeyError, TypeError):
        return default


def set_config_value(config: Dict, path: str, value: Any) -> None:
    """Set configuration value using dot notation path.

    Args:
        config: Configuration dictionary
        path: Configuration path (e.g., "machine.bed_size_x")
        value: Value to set
    """
    parts = path.split(".")
    current = config

    # Navigate to the parent of the target
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]

    # Set the value
    current[parts[-1]] = value


def save_config(config: Dict, config_file: Union[str, Path]) -> bool:
    """Save configuration to YAML file.

    Args:
        config: Configuration dictionary
        config_file: Path to YAML configuration file

    Returns:
        True if config was saved successfully, False otherwise
    """
    config_path = Path(config_file)

    try:
        # Create directory if it doesn't exist
        os.makedirs(config_path.parent, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved configuration to {config_path}")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False


def validate_config(config: Dict) -> bool:
    """Validate configuration.

    Args:
        config: Configuration dictionary

    Returns:
        True if configuration is valid, False otherwise
    """
    # Check required sections
    required_sections = ["machine", "gcode", "svg", "tools"]
    for section in required_sections:
        if section not in config:
            logger.error(f"Missing required configuration section: {section}")
            return False

    # Check machine settings
    machine = config.get("machine", {})
    if not machine.get("bed_size_x") or not machine.get("bed_size_y"):
        logger.error("Machine bed size not specified")
        return False

    # Check tool settings
    tools = config.get("tools", {})
    if not tools:
        logger.error("No tools configured")
        return False

    return True 