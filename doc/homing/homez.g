; homez.g – Final version with proper scaling and working zero

M564 H0                       ; Allow movement before homing
G90                           ; Absolute positioning
G91                           ; Relative mode

; Only move up if Z endstop not already triggered
if !move.axes[2].homed || sensors.endstops[2].triggered = false
  G1 H1 Z100 F500             ; Move up until switch
  G1 Z-5 F300                 ; Back off
  G1 H1 Z10 F300              ; Re-home slowly

G90
G92 Z84                       ; Declare Z max

; Optional descent
; G1 Z1 F600
; G92 Z1