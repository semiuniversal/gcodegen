"""
Airbrush-specific functionality for the H.Airbrush device.

This module contains functionality specific to the H.Airbrush dual-airbrush plotter,
including tool changes and a deterministic mapping from stroke parameters to
machine controls (Z for width, feedrate for opacity, paint flow for fine tuning)
with per-tool calibration.
"""

import math
import logging
from typing import Dict, List, Tuple, Optional

# Set up logging
logger = logging.getLogger(__name__)


class AirbrushController:
    """Controller for H.Airbrush dual-airbrush plotter."""

    def __init__(self, config: Dict = None):
        """Initialize airbrush controller.

        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or {}

        # Machine parameters
        self.machine_width = self.config.get("machine", {}).get("bed_size_x", 700)
        self.machine_height = self.config.get("machine", {}).get("bed_size_y", 1000)
        self.machine_z_min = 0.0
        self.machine_z_max = 84.0

        # Z height parameters
        self.z_min = float(self.config.get("machine", {}).get("z_min", 5.0))
        self.z_max = float(self.config.get("machine", {}).get("z_max", 80.0))
        self.z_travel = float(self.config.get("machine", {}).get("safe_z", 10.0))
        self.safe_z_threshold = float(self.config.get("machine", {}).get("safe_z", 10.0))

        # Speed parameters
        self.travel_speed = float(self.config.get("machine", {}).get("travel_speed", 24000))
        self.default_drawing_speed = float(self.config.get("machine", {}).get("work_speed", 12000))
        self.z_speed = float(self.config.get("machine", {}).get("z_speed", 1200))
        # Track current Z to avoid unnecessary retracts/lowers
        self.current_z: float = self.safe_z_threshold

        # U/V axis parameters for stepper motor flow control
        self.u_axis_min = float(self.config.get("u_axis", {}).get("min", 0.0))
        self.u_axis_max = float(self.config.get("u_axis", {}).get("max", 4.0))
        self.u_axis_dead_zone = float(self.config.get("u_axis", {}).get("dead_zone", 0.8))
        self.u_axis_feedrate = float(self.config.get("u_axis", {}).get("feedrate", 200))

        self.v_axis_min = float(self.config.get("v_axis", {}).get("min", 0.0))
        self.v_axis_max = float(self.config.get("v_axis", {}).get("max", 4.0))
        self.v_axis_dead_zone = float(self.config.get("v_axis", {}).get("dead_zone", 0.8))
        self.v_axis_feedrate = float(self.config.get("v_axis", {}).get("feedrate", 200))

        # Deterministic model parameters
        # Spray cone geometry for width -> Z mapping
        self.spray_cone_angle = float(self.config.get("airbrush", {}).get("spray_cone_angle", 15.0))
        self.spray_cone_factor = math.tan(math.radians(self.spray_cone_angle / 2.0))

        # Opacity -> speed mapping defaults
        self.feedrate_min_default = float(self.config.get("airbrush", {}).get("feedrate_min", 6000.0))
        self.feedrate_max_default = float(self.config.get("airbrush", {}).get("feedrate_max", self.travel_speed))
        self.opacity_speed_gamma_default = float(self.config.get("airbrush", {}).get("opacity_speed_gamma", 1.8))

        # Paint flow computation defaults
        self.flow_min_default = float(self.config.get("airbrush", {}).get("flow_min", 0.10))
        self.flow_max_default = float(self.config.get("airbrush", {}).get("flow_max", 1.00))
        self.flow_width_factor_default = float(self.config.get("airbrush", {}).get("flow_width_factor", 0.05))

        # Brush state tracking
        self.brush_a_active = False
        self.brush_b_active = False
        self.current_brush = None

        # Tool offsets (firmware-configured; included for documentation)
        self.head_offsets = self.config.get("machine", {}).get("head_offsets", {
            "tool0": {"x": 0.0, "y": 0.0},
            "tool1": {"x": 10.0, "y": 0.0},
        })

    # -------------------------
    # Helpers
    # -------------------------
    def _normalize_color(self, color: str) -> str:
        if not color:
            return ""
        c = color.strip().lower()
        if c in ["black", "#000", "#000000"]:
            return "#000000"
        if c in ["white", "#fff", "#ffffff"]:
            return "#ffffff"
        # Treat any non-white as black by default (two-color device)
        return "#000000" if c != "#ffffff" else "#ffffff"

    def _resolve_tool_for_color(self, stroke_color: str) -> Tuple[str, Dict]:
        tools_cfg = self.config.get("tools", {}) or {}
        normalized = self._normalize_color(stroke_color)
        # Try exact color match in tools
        for tool_key, tool_cfg in tools_cfg.items():
            tool_color = self._normalize_color(tool_cfg.get("color", ""))
            if tool_color == normalized:
                brush_id = "A" if tool_key.lower() == "tool0" else "B"
                return brush_id, tool_cfg
        # Fallback
        if normalized == "#ffffff":
            return "B", tools_cfg.get("tool1", {})
        return "A", tools_cfg.get("tool0", {})

    def _maybe_raise_to_safe(self, commands: List[str]) -> None:
        """Raise to safe Z only if current Z is below the safe threshold.

        Updates `self.current_z` if a move is emitted.
        """
        if self.current_z < self.safe_z_threshold:
            commands.append(f"G1 Z{self.z_travel:.3f} F{self.z_speed:.3f} ; Raise to safe Z if below threshold")
            commands.append("M400 ; Wait for Z movement to complete")
            self.current_z = self.z_travel

    # -------------------------
    # Machine lifecycle G-code
    # -------------------------
    def generate_machine_initialization(self) -> List[str]:
        commands: List[str] = []
        commands.append("; H.Airbrush Dual-Airbrush Plotter G-code")
        commands.append("; Generated by GCodeGen")
        commands.append("M451 ; CNC mode")
        commands.append("G17 ; X-Y plane")
        commands.append("G21 ; mm units")
        commands.append("G90 ; Absolute positioning")
        commands.append("M17 ; Enable all motors")
        commands.append("M564 H1 S1 ; Enforce soft limits and require homing")

        skip_homing = bool(self.config.get("machine", {}).get("skip_homing", False))
        if not skip_homing:
            commands.append("G28 ; Home X, Y, Z axes")
            commands.append("G28 U ; Home U axis (Brush A flow control)")
            commands.append("G28 V ; Home V axis (Brush B flow control)")

        # Initialize Z only if needed
        if self.current_z < self.safe_z_threshold:
            commands.append(f"G1 Z{self.z_travel:.3f} F{self.z_speed:.3f} ; Raise to safe Z at init")
            commands.append("M400 ; Wait for Z movement to complete")
            self.current_z = self.z_travel
        commands.append(f"G92 Z{self.current_z:.3f} ; Set Z height")
        commands.append("M84 S0 ; No stepper timeout")

        commands.append("; ===== AIRBRUSH SYSTEM INITIALIZATION =====")
        commands.append("; 1. Turn off all air solenoids")
        commands.append("M106 P2 S0 ; Brush A air off")
        commands.append("M106 P3 S0 ; Brush B air off")
        commands.append("G4 P500 ; Wait for air to stop completely")
        commands.append("; 2. Ensure U and V axes are at minimum position (closed)")
        commands.append(f"G1 U{self.u_axis_min:.3f} F{self.u_axis_feedrate} ; Close Brush A flow")
        commands.append(f"G1 V{self.v_axis_min:.3f} F{self.v_axis_feedrate} ; Close Brush B flow")
        commands.append("M400 ; Wait for stepper motion to complete")

        commands.append("; --- Tool Selection ---")
        commands.append("T0 ; Select Tool 0 (Brush A) as the default tool")
        # Removed G4 dwell after tool selection to reduce runtime
        commands.append("; STEPPER AND FAN CONFIGURATION:")
        commands.append("; - Brush A: Air=Fan2, Flow=U axis (0.0-4.0mm, dead zone 0.0-0.8mm)")
        commands.append("; - Brush B: Air=Fan3, Flow=V axis (0.0-4.0mm, dead zone 0.0-0.8mm)")
        commands.append("; ===== END AIRBRUSH SYSTEM INITIALIZATION =====")
        commands.append("")
        return commands

    def generate_machine_cleanup(self) -> List[str]:
        commands: List[str] = []
        commands.append("; ===== MACHINE CLEANUP =====")
        self._maybe_raise_to_safe(commands)
        commands.append("; Return to home position with Tool 0")
        commands.append("T0 ; Select Tool 0 (Brush A)")
        # Removed G4 dwell after tool selection to reduce runtime
        commands.append("G0 X0 Y0 F24000")
        commands.append("M400 ; Wait for movement to complete")
        commands.append("M564 H1 S1 ; Enforce soft limits")
        commands.append("; Turn off all airbrush systems")
        commands.append(f"G1 U{self.u_axis_min:.3f} F{self.u_axis_feedrate} ; Close Brush A flow")
        commands.append(f"G1 V{self.v_axis_min:.3f} F{self.v_axis_feedrate} ; Close Brush B flow")
        commands.append("M106 P2 S0 ; Brush A air off")
        commands.append("M106 P3 S0 ; Brush B air off")
        commands.append("G4 P500 ; Allow air to stop completely")
        commands.append("M18 ; Disable all motors")
        commands.append("; End of G-code")
        return commands

    def start_brush(self, brush_id: str) -> List[str]:
        if brush_id not in ["A", "B"]:
            raise ValueError("brush_id must be 'A' or 'B'")
        commands: List[str] = []
        commands.append(f"; START BRUSH {brush_id}")
        tool_number = 0 if brush_id == "A" else 1
        # Only raise if below safe before tool change
        self._maybe_raise_to_safe(commands)
        commands.append(f"T{tool_number} ; Select Tool {tool_number} (Brush {brush_id})")
        # Removed G4 dwell after tool change to reduce runtime
        if brush_id == "B":
            commands.append("M564 H0 S0 ; Disable soft limits for Tool 1 movements")
            # Removed brief pause after changing limits
        if brush_id == "A":
            self.brush_a_active = True
            self.current_brush = "A"
        else:
            self.brush_b_active = True
            self.current_brush = "B"
        return commands

    def stop_brush(self, brush_id: str) -> List[str]:
        if brush_id not in ["A", "B"]:
            raise ValueError("brush_id must be 'A' or 'B'")
        commands: List[str] = []
        commands.append(f"; STOP BRUSH {brush_id}")
        if brush_id == "A":
            axis = "U"
            air_fan = 2
            axis_min = self.u_axis_min
            axis_feedrate = self.u_axis_feedrate
        else:
            axis = "V"
            air_fan = 3
            axis_min = self.v_axis_min
            axis_feedrate = self.v_axis_feedrate
        # Close paint flow while still moving handled in path logic; here ensure closed
        commands.append(f"G1 {axis}{axis_min:.3f} F{axis_feedrate} ; Close Brush {brush_id} flow")
        commands.append(f"M106 P{air_fan} S0 ; Brush {brush_id} air off")
        if brush_id == "B":
            # Only raise if needed before restoring limits
            self._maybe_raise_to_safe(commands)
            commands.append("M564 H1 S1 ; Restore soft limits after using Tool 1")
        else:
            # Only raise if needed after stopping brush
            self._maybe_raise_to_safe(commands)
        if brush_id == "A":
            self.brush_a_active = False
        else:
            self.brush_b_active = False
        self.current_brush = None
        return commands

    # -------------------------
    # Deterministic parameter mapping
    # -------------------------
    def calculate_airbrush_parameters(self, stroke_width: float, stroke_opacity: float, tool_cfg: Optional[Dict] = None) -> Tuple[float, float, float]:
        """Compute (z_height, paint_flow, feedrate) deterministically.

        - Width is controlled only by Z via spray cone geometry.
        - Opacity maps primarily to feedrate (faster = lighter); secondarily to flow.
        - Per-tool calibration supported via tool_cfg overrides.
        """
        # Width -> Z
        z_from_width = stroke_width / (2.0 * self.spray_cone_factor) if self.spray_cone_factor > 0 else self.z_min
        # Clamp to configured Z bounds (respect config z_max)
        z_height = max(self.z_min, min(self.z_max, z_from_width))

        # Opacity -> feedrate
        v_min = float(tool_cfg.get("v_min", self.feedrate_min_default)) if isinstance(tool_cfg, dict) else self.feedrate_min_default
        v_max = float(tool_cfg.get("v_max", self.feedrate_max_default)) if isinstance(tool_cfg, dict) else self.feedrate_max_default
        gamma = float(tool_cfg.get("opacity_gamma", self.opacity_speed_gamma_default)) if isinstance(tool_cfg, dict) else self.opacity_speed_gamma_default
        o = max(0.0, min(1.0, float(stroke_opacity)))
        feedrate = v_min + ((1.0 - o) ** gamma) * max(0.0, v_max - v_min)

        # Opacity/width -> flow
        flow_min = float(tool_cfg.get("p_min", self.flow_min_default)) if isinstance(tool_cfg, dict) else self.flow_min_default
        flow_max = float(tool_cfg.get("p_max", self.flow_max_default)) if isinstance(tool_cfg, dict) else self.flow_max_default
        k_w = float(tool_cfg.get("flow_width_factor", self.flow_width_factor_default)) if isinstance(tool_cfg, dict) else self.flow_width_factor_default
        w_min = float(tool_cfg.get("min_width", 1.0)) if isinstance(tool_cfg, dict) else 1.0
        w_max = float(tool_cfg.get("max_width", max(w_min + 1.0, stroke_width))) if isinstance(tool_cfg, dict) else max(w_min + 1.0, stroke_width)
        norm_width = 0.0
        if w_max > w_min:
            norm_width = max(0.0, min(1.0, (stroke_width - w_min) / (w_max - w_min)))
        base_flow = flow_min + o * (flow_max - flow_min) + k_w * norm_width
        flow_scale = float(tool_cfg.get("flow_scale", 1.0)) if isinstance(tool_cfg, dict) else 1.0
        flow_offset = float(tool_cfg.get("flow_offset", 0.0)) if isinstance(tool_cfg, dict) else 0.0
        paint_flow = max(flow_min, min(flow_max, base_flow * flow_scale + flow_offset))

        return z_height, paint_flow, feedrate

    # -------------------------
    # Path G-code generation
    # -------------------------
    def generate_path_commands(self, polyline: List[Tuple[float, float]], stroke_color: str, stroke_width: float, stroke_opacity: float, base_feedrate: Optional[float] = None) -> List[str]:
        if not polyline or len(polyline) < 2:
            return ["; WARNING: Path has fewer than 2 points, skipping."]

        commands: List[str] = []

        # Resolve brush/tool and tool config
        brush_id, tool_cfg = self._resolve_tool_for_color(stroke_color)

        # Enforce tool-specific min/max width with safety: swap if misordered
        min_w = float(tool_cfg.get("min_width", stroke_width)) if isinstance(tool_cfg, dict) else stroke_width
        max_w = float(tool_cfg.get("max_width", stroke_width)) if isinstance(tool_cfg, dict) else stroke_width
        if max_w < min_w:
            commands.append(f"; WARNING: tool min/max width misordered (min={min_w:.2f}, max={max_w:.2f}); swapping")
            min_w, max_w = max_w, min_w
        effective_width = stroke_width
        # Clamp to [min_w, max_w]
        before = effective_width
        if effective_width < min_w:
            effective_width = min_w
        elif effective_width > max_w:
            effective_width = max_w
        if abs(effective_width - before) > 1e-6:
            commands.append(f"; Width clamped from {before:.2f}mm to {effective_width:.2f}mm within [{min_w:.2f},{max_w:.2f}] mm")

        # Compute deterministic parameters
        z_height, paint_flow, feedrate = self.calculate_airbrush_parameters(effective_width, stroke_opacity, tool_cfg)

        # Axis mapping
        if brush_id == 'A':
            axis = 'U'
            air_fan = 2
            axis_min = self.u_axis_min
            axis_max = self.u_axis_max
            axis_dead = self.u_axis_dead_zone
            axis_feed = self.u_axis_feedrate
        else:
            axis = 'V'
            air_fan = 3
            axis_min = self.v_axis_min
            axis_max = self.v_axis_max
            axis_dead = self.v_axis_dead_zone
            axis_feed = self.v_axis_feedrate

        # Flow position in mm (within dead_zone..max)
        flow_position = axis_dead + (paint_flow * (axis_max - axis_dead))
        flow_position = max(axis_min, min(axis_max, flow_position))

        # Stroke information
        commands.append("; ===== STROKE PARAMETERS =====")
        commands.append(f"; Color: {stroke_color}")
        commands.append(f"; Width: {effective_width:.2f}mm")
        commands.append(f"; Opacity: {stroke_opacity:.2f}")
        commands.append(f"; Brush: {brush_id}")
        commands.append(f"; Z-height: {z_height:.2f}mm")
        commands.append(f"; Paint flow: {paint_flow:.2f} -> {axis}{flow_position:.3f}mm")
        commands.append(f"; Feedrate: {feedrate:.1f}mm/min")

        # Start brush (tool and soft limits handling)
        commands.extend(self.start_brush(brush_id))

        # Pre-travel Z handling: only RAISE if needed; never lower to safe before travel
        # - If current Z < safe, raise to max(safe, next drawing Z)
        # - Else if current Z >= safe but < next drawing Z, raise to drawing Z
        pre_travel_target_z: Optional[float] = None
        if self.current_z < self.safe_z_threshold:
            pre_travel_target_z = max(self.safe_z_threshold, z_height)
        elif self.current_z < z_height:
            pre_travel_target_z = z_height
        if pre_travel_target_z is not None and pre_travel_target_z > self.current_z:
            commands.append(f"G1 Z{pre_travel_target_z:.3f} F{self.z_speed:.3f}")
            commands.append("M400 ; Wait for Z movement to complete")
            self.current_z = pre_travel_target_z

        # Rapid to start point at travel speed (current Z is guaranteed >= min(safe, z_height))
        x0, y0 = polyline[0]
        commands.append(f"G0 X{x0:.3f} Y{y0:.3f} F{self.travel_speed:.3f}")
        commands.append("M400 ; Wait for XY movement to complete")

        # Descend or adjust to drawing Z if needed (safe to lower after travel)
        if abs(self.current_z - z_height) > 1e-6:
            commands.append(f"G1 Z{z_height:.3f} F{self.z_speed:.3f}")
            commands.append("M400 ; Wait for Z movement to complete")
            self.current_z = z_height

        # Set feedrate once per stroke, then start air
        commands.append(f"G1 F{feedrate:.3f}")
        commands.append(f"M106 P{air_fan} S1 ; Air on at motion start")

        # Draw path; first move also ramps U/V to target flow to avoid start dot
        first = True
        for x, y in polyline[1:]:
            if first:
                commands.append(f"G1 X{x:.3f} Y{y:.3f} {axis}{flow_position:.3f}")
                first = False
            else:
                commands.append(f"G1 X{x:.3f} Y{y:.3f}")

        commands.append("M400 ; Wait for drawing to complete")

        # Stop brush: close flow then air off (no extra dwell)
        commands.extend(self.stop_brush(brush_id))

        commands.append("; === PATH END ===\n")
        return commands 