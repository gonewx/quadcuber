"""Source locations and an explicit, relocatable mechanical output directory."""
import os
from pathlib import Path

MECHANICAL = Path(__file__).resolve().parent
ROOT = MECHANICAL.parent
INPUTS = MECHANICAL / 'inputs'
ASSEMBLY = MECHANICAL / 'assembly'
OUTPUT = Path(os.environ.get('QUADCUBER_MECHANICAL_OUTPUT', ROOT / 'generated/mechanical')).resolve()
MANUAL_OUTPUT = OUTPUT / 'manual'
