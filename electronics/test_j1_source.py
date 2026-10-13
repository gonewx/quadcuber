"""Independent input-connector electrical contract; physical checks are separate."""
import runpy
import unittest
from pathlib import Path

C = {c['ref']: c for c in runpy.run_path(str(Path(__file__).with_name('circuit.py')))['C']}


class InputConnectorContract(unittest.TestCase):
    def test_center_positive_and_unused_sleeve_switch(self):
        self.assertEqual(C['J1']['mpn'], 'RASPC722X')
        self.assertEqual(C['J1']['mfr'], 'Switchcraft')
        self.assertEqual(C['J1']['pins'], {'1': 'VIN', '2': 'GND', '3': None})
        self.assertEqual(C['J1']['names'], {'1': 'CENTER_9V', '2': 'SLEEVE_GND', '3': 'SLEEVE_SHUNT_NC'})

    def test_original_input_protection_is_retained(self):
        self.assertEqual(C['F1']['mpn'], '0407008.WR')
        self.assertEqual(C['F1']['pins'], {'1': 'VIN', '2': 'VIN_FUSED'})
        self.assertEqual(C['D4']['mpn'], 'SMBJ12CA')
        self.assertEqual(C['D4']['pins'], {'1': 'VIN_FUSED', '2': 'GND'})
        self.assertEqual(C['D3']['pins'], {'1': 'VM', '2': 'GND'})


if __name__ == '__main__':
    unittest.main()
