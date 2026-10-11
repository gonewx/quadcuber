#!/usr/bin/env python3
"""Record nominal 1.6mm four-layer stackup; dielectric details need fabricator approval."""
from pathlib import Path
p=Path(__file__).resolve().parent/'quadcuber.kicad_pcb';s=p.read_text()
if '(stackup' not in s:
 s=s.replace('(setup','''(setup
  (stackup
   (layer "F.SilkS" (type "Top Silk Screen"))
   (layer "F.Paste" (type "Top Solder Paste"))
   (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
   (layer "F.Cu" (type "copper") (thickness 0.07))
   (layer "dielectric 1" (type "prepreg") (thickness 0.18) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
   (layer "In1.Cu" (type "copper") (thickness 0.035))
   (layer "dielectric 2" (type "core") (thickness 1.01) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
   (layer "In2.Cu" (type "copper") (thickness 0.035))
   (layer "dielectric 3" (type "prepreg") (thickness 0.18) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
   (layer "B.Cu" (type "copper") (thickness 0.07))
   (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
   (layer "B.Paste" (type "Bottom Solder Paste"))
   (layer "B.SilkS" (type "Bottom Silk Screen"))
   (copper_finish "ENIG")
   (dielectric_constraints no)
  )''',1);p.write_text(s)
