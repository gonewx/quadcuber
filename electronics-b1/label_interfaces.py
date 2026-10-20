#!/usr/bin/env python3
"""给已布线的 B1 PCB 补接口丝印（舵机 G/+/S、J2 UART、EV3 背面第 1 针），不动铜和元件。用 KiCad 10 自带 Python 运行。"""
import sys
from pathlib import Path

import pcbnew as p

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from circuit import REF_MOVES, SILK  # noqa: E402
from silk import add_labels, move_refs  # noqa: E402

PCB = HERE / 'quadcuber-b1.kicad_pcb'
b = p.LoadBoard(str(PCB))
add_labels(b, SILK, 50.0, 50.0)
move_refs(b, REF_MOVES, 50.0, 50.0)
p.SaveBoard(str(PCB), b)
print(f'B1: {len(SILK)} 条接口丝印')
