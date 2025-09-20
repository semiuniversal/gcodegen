; homeu.g — Revised homing for Flow A axis (U)

M564 H0
G91                             ; Relative mode

G1 H1 U-20 F100                 ; Slow seek toward endstop
G1 U2 F200                      ; Back off
G1 H1 U-5 F100                  ; Re-approach until switch triggers again

G92 U0                          ; Define as home
G90                             ; Back to absolute
