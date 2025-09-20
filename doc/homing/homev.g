; homev.g — Revised homing for Flow B axis (V)

M564 H0
G91                             ; Relative mode

G1 H1 V-20 F100                 ; Slow seek toward endstop
G1 V2 F200                      ; Back off
G1 H1 V-5 F100                  ; Re-approach until switch triggers again

G92 V0                          ; Define as home
G90                             ; Back to absolute
