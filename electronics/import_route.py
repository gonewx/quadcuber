#!/usr/bin/env python3
"""Import a reviewed Specctra session and refill native KiCad zones."""
import sys,pcbnew as p
from pathlib import Path
H=Path(__file__).resolve().parent
b=p.LoadBoard(str(H/'quadcuber.kicad_pcb'))
assert p.ImportSpecctraSES(b,sys.argv[1]),'Session import failed'
f=p.ZONE_FILLER(b);f.Fill(b.Zones())
p.SaveBoard(str(H/'quadcuber.kicad_pcb'),b)
print('Imported tracks and refilled planes:',len(b.GetTracks()))
