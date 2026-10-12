"""Assembly output must not request placement of zero-quantity/DNP parts."""
import csv
import unittest
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'generated/electronics'


class AssemblyExportContract(unittest.TestCase):
    def test_default_cpl_exactly_matches_populated_bom(self):
        with (OUT / 'bom.csv').open(newline='') as f:
            wanted = {r['Reference'] for r in csv.DictReader(f) if int(r['Quantity']) > 0}
        with (OUT / 'positions.csv').open(newline='') as f:
            actual = [r['Ref'] for r in csv.DictReader(f)]
        self.assertEqual(len(actual), len(set(actual)), 'Duplicate placement reference')
        self.assertSetEqual(set(actual), wanted)


if __name__ == '__main__':
    unittest.main()
