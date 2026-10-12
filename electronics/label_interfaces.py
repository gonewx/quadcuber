#!/usr/bin/env python3
"""Readable connector polarity and scope-point legends; recheck silk DRC."""
import pcbnew as p
from pathlib import Path
H=Path(__file__).resolve().parent;b=p.LoadBoard(str(H/'quadcuber.kicad_pcb'))
for d in list(b.GetDrawings()):
 if isinstance(d,p.PCB_TEXT) and d.GetText()=='G + S':b.Delete(d)
labels=[]
for idx in range(4):
 x=15+34*idx
 for j,n in enumerate(['G','+','S']):labels.append((n,x+15.5,97+j*2.54,.8))
 for j,n in enumerate(['M1','M2','A','B']):labels.append((n,6+idx*34+j*5,64.7,.8))
for j,n in enumerate(['GND','VM','5A','5B','ENC','3V3','VSYS']):labels.append((n,84+j*7,63.3,.8))
labels.extend([('+9V',45,16,.8),('GND',50.08,16,.8),('G',3.8,57,.8),('TX',3.8,59.54,.8),('RX',3.8,62.08,.8),('RUN',28.5,61,.8)])
labels.extend([('BOOT',7,6,.8),('RESET',7,48.5,.8),('USB',27,2,.8),('SWD',18.8,50.8,.8),('3V3',15,52.8,.8),('IO',17.54,52.8,.8),('G',20.08,52.8,.8),('CLK',22.62,52.8,.8),('GP25',28,18.3,.8)])
for text,x,y,size in labels:
 pos=p.VECTOR2I(p.FromMM(50+x),p.FromMM(50+y))
 if any(isinstance(d,p.PCB_TEXT) and d.GetText()==text and d.GetPosition()==pos for d in b.GetDrawings()):continue
 t=p.PCB_TEXT(b);t.SetText(text);t.SetPosition(pos);t.SetTextSize(p.VECTOR2I(p.FromMM(size),p.FromMM(size)));t.SetTextThickness(p.FromMM(.12));t.SetLayer(p.F_SilkS);b.Add(t)
p.SaveBoard(str(H/'quadcuber.kicad_pcb'),b)
