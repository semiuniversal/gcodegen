; homeall.g — precise homing with dead zone avoidance and logical origin reset

M564 H0                          ; Allow movement before homing
G90                              ; Absolute positioning
G92 Z0                           ; Clear Z state (defensive)

; --- Step 1: Home Z to max ---
M98 P"homez.g"                   ; Handles Z homing and G92 Z84
M117 Homing Step 1 Complete

; --- Step 2: Select reference tool (Brush A) ---
T0 P0 R0                         ; Select Tool 0 (no reset)
M117 Homing Step 2 Complete

; --- Step 3: Escape cleaning zone vertically before any XY homing ---
G91
G1 Y150 F3000                    ; Raise Y to clear steppers
G90
M117 Homing Step 3 Complete

; --- Step 4: Home X axis ---
G91
G1 H1 X-1000 F3000               ; Seek X min
G1 X5 F3000                      ; Back off
G1 H1 X-10 F1000                 ; Re-seek slowly
G1 X81 F3000                     ; Move to X81 for safe Y homing
G90
M117 Homing Step 4 Complete

; --- Step 5: Home Y axis ---
G91
G1 H1 Y-1500 F3000               ; Seek Y min
G1 Y5 F3000                      ; Back off
G1 H1 Y-10 F1000                 ; Re-seek slowly
G90
M117 Homing Step 5 Complete

; --- Step 6: Move to constrained logical origin ---
G1 X100 Y120 F3000                ; Move to working origin (safe)
G92 X0 Y0                        ; Set logical origin
M117 Homing Step 6 Complete

; --- Step 7: Re-enable homing enforcement ---
M564 H1 S1                       ; Lock motion to homed axes
M117 Homing Sequence Complete

; --- Step 8: Home paint steppers
M98 P"homeu.g"                   ; Handles A paint flow homing
M98 P"homev.g"                   ; Handles B paint flow homing

; --- Optional: Confirm limits ---
M208