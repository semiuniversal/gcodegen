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


def _is_number(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _collect_config_errors(config: Dict) -> list:
    """Return a list of human-friendly validation errors."""
    errors = []

    # Required sections
    for section in ["machine", "gcode", "svg", "tools", "airbrush"]:
        if section not in config:
            errors.append(f"Missing required section '{section}'.")
    if errors:
        return errors

    machine = config.get("machine", {})
    svg = config.get("svg", {})
    airbrush = config.get("airbrush", {})
    tools = config.get("tools", {})

    # Machine required keys
    for key in ["travel_speed", "z_min", "z_max", "safe_z"]:
        if key not in machine or not _is_number(machine.get(key)):
            errors.append(f"machine.{key} must be provided and numeric.")
    if not errors:
        z_min = float(machine["z_min"])
        z_max = float(machine["z_max"])
        safe_z = float(machine["safe_z"])
        travel = float(machine["travel_speed"])
        if z_min <= 0:
            errors.append("machine.z_min must be > 0.")
        if z_max <= z_min:
            errors.append("machine.z_max must be greater than machine.z_min.")
        if safe_z <= 0:
            errors.append("machine.safe_z must be > 0.")
        if travel <= 0:
            errors.append("machine.travel_speed must be > 0.")

    # SVG required keys
    for key in ["curve_resolution", "max_segment_length_mm"]:
        if key not in svg or not _is_number(svg.get(key)):
            errors.append(f"svg.{key} must be provided and numeric.")
    if not errors and float(svg.get("curve_resolution", 0)) < 8:
        errors.append("svg.curve_resolution should be >= 8.")
    if not errors and float(svg.get("max_segment_length_mm", 0)) <= 0:
        errors.append("svg.max_segment_length_mm must be > 0.")

    # Airbrush required keys (no global viscosity/flow bounds)
    for key in ["opacity_speed_gamma", "feedrate_z_exponent", "feedrate_floor"]:
        if key not in airbrush or not _is_number(airbrush.get(key)):
            errors.append(f"airbrush.{key} must be provided and numeric.")
    if not errors:
        if float(airbrush.get("opacity_speed_gamma", 0)) <= 0:
            errors.append("airbrush.opacity_speed_gamma must be > 0.")
        if float(airbrush.get("feedrate_z_exponent", -1)) < 0:
            errors.append("airbrush.feedrate_z_exponent must be >= 0.")
        if float(airbrush.get("feedrate_floor", 0)) <= 0:
            errors.append("airbrush.feedrate_floor must be > 0.")

    # Tools required keys (per-tool viscosity and flow bounds)
    for tool_name in ["tool0", "tool1"]:
        if tool_name not in tools:
            errors.append(f"tools.{tool_name} missing.")
            continue
        t = tools[tool_name]
        for key in ["min_width", "max_width", "v_max", "viscosity", "p_min", "p_max"]:
            if key not in t or (key != "viscosity" and not _is_number(t.get(key))):
                errors.append(f"tools.{tool_name}.{key} must be provided and numeric.")
        # Range checks when available
        min_w = t.get("min_width")
        max_w = t.get("max_width")
        if _is_number(min_w) and _is_number(max_w) and float(max_w) < float(min_w):
            errors.append(f"tools.{tool_name}.max_width must be >= min_width.")
        vmax = t.get("v_max")
        visc = t.get("viscosity")
        if visc is None or not _is_number(visc) or not (0.0 <= float(visc) <= 1.0):
            errors.append(f"tools.{tool_name}.viscosity must be between 0.0 and 1.0.")
        pmin = t.get("p_min")
        pmax = t.get("p_max")
        if _is_number(pmin) and _is_number(pmax) and float(pmax) < float(pmin):
            errors.append(f"tools.{tool_name}.p_max must be >= p_min.")

    return errors


def validate_config(config: Dict) -> bool:
    """Validate configuration and log actionable errors."""
    errors = _collect_config_errors(config)
    if errors:
        logger.error("Configuration validation failed:")
        for err in errors:
            logger.error(f" - {err}")
        logger.error("See gcodegen/default_config.yaml for reference values.")
        return False
    return True