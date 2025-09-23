; Configuration file for Duet 2 WiFi (RepRapFirmware 3.4.6)
; Machine: CoreXY-H Dual-Airbrush Plotter

;---------------------------
; General Setup
;---------------------------
G90                            ; Absolute positioning
M83                            ; Relative extruder moves (not used)
M550 P"H.Airbrush"             ; Set machine name
M555 P2                        ; Set Marlin-style output
M451                           ; Enable CNC mode

;---------------------------
; Networking
;---------------------------
M552 S1                        ; Enable WiFi

;---------------------------
; Z Axis (internal driver E1)
;---------------------------
M569 P2 S0                     ; Z motor direction (invert if needed)
M584 Z2                        ; Map Z axis to internal driver (E1)
M92 Z3235.41                   ; Z steps/mm (calibrated)
M906 Z800 I30                  ; Z motor current
M203 Z1200                     ; Z max speed = 20 mm/s
M201 Z300                      ; Z acceleration
M566 Z60                       ; Z jerk

;---------------------------
; Flow Axis Configuration (U = Flow A, V = Flow B)
;---------------------------
; Stepper-driven paint flow control axes

; --- Map U and V axes ---
M584 U3 V4                       ; U on E3, V on E4

; --- Stepper direction ---
M569 P3 S1                       ; U direction
M569 P4 S1                       ; V direction

; --- Motion parameters ---
M92 U85 V85                      ; Steps/mm for ~12mm spool
M906 U350 V350 I80               ; Prevent these little guys from cooking
M203 U500 V500                   ; Max speed = ~8 mm/s
M201 U100 V100                   ; Acceleration
M566 U20 V20                     ; Jerk

; --- Endstops ---
M574 U1 S1 P"e0stop"             ; Normally open, active-high
M574 V1 S1 P"e1stop"             ; Normally open, active-high

; --- Motion limits ---
M208 U0 S1                       ; U min
M208 U4 S0                       ; U max
M208 V0 S1                       ; V min
M208 V4 S0                       ; V max

;---------------------------
; CoreXY Axes (external drivers on E2/E3)
;---------------------------
M569 P5 S0                     ; X motor (Drive 5 - E2)
M569 P6 S0                     ; Y motor (Drive 6 - E3)
M584 X5 Y6                     ; Map CoreXY axes
M669 K1                        ; Enable CoreXY mode
M92 X10.04 Y10.04              ; CoreXY steps/mm (calibrated)
M203 X24000 Y24000             ; Max speed: 400 mm/s
M201 X1200 Y1200               ; Acceleration: reduced for less shake
M566 X60 Y60                   ; Jerk: ~1 mm/s — softened to reduce head snap

; Optional: Tune step pulse width for external drivers
M569 P5 T10:10:5:0
M569 P6 T10:10:5:0

;---------------------------
; Motion Limits
;---------------------------
M208 X0 Y0 Z0 S1             ; origin = safe offset
M208 X695 Y1080 Z84 S0       ; (X 795-100, Y 1150-70)
M564 H1 S1                     ; Enforce limits and require homing

;---------------------------
; Endstops
;---------------------------
M574 X1 S1 P"!xstop"           ; X min, active-low
M574 Y1 S1 P"!ystop"           ; Y min, active-low
M574 Z2 S1 P"!zstop"           ; Z max, active-low

;---------------------------
; Z-Probe (not used)
;---------------------------
M558 P0 H0 F0 T0               ; Disable Z probe

;---------------------------
; Solenoid PWM Assignments
;---------------------------
M950 F2 C"fan1"                ; Solenoid A on Fan1
M950 F3 C"fan2"                ; Solenoid B on Fan2
M106 P2 H-1                    ; Disable thermostatic mode (Solenoid A)
M106 P3 H-1                    ; Disable thermostatic mode (Solenoid B)
M106 P2 S0                     ; Solenoid A OFF
M106 P3 S0                     ; Solenoid B OFF

; Usage:
; M106 P2 S1.0        ; Turn ON Solenoid A
; M106 P3 S1.0        ; Turn ON Solenoid B
; M106 P2 S0          ; Turn OFF Solenoid A
; M106 P3 S0          ; Turn OFF Solenoid B
; M98 P"a-air-on.g"   ; Macro: Solenoid A ON
; M98 P"b-air-on.g"   ; Macro: Solenoid B ON
; M98 P"a-air-off.g"  ; Macro: Solenoid A OFF
; M98 P"b-air-off.g"  ; Macro: Solenoid B OFF



;---------------------------
; Tool Definitions
;---------------------------
; Brush A (Black)
M563 P0 S"Brush A" F2

; Brush B (White)
M563 P1 S"Brush B" F3
; Clear any residual tool offsets
G10 P0 X0 Y0 Z0
G10 P1 X100 Y-25 Z0
;---------------------------
; Misc
;---------------------------
;M501                           ; Load config-override.g (if present)