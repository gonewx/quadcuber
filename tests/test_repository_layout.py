"""Independent frozen bytes survive the repository layout migration."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RepositoryLayout(unittest.TestCase):
    def test_frozen_deliverables_and_protected_inputs(self):
        baseline = json.loads((ROOT / 'mechanical/inputs/layout-baseline.json').read_text())
        for row in baseline['files']:
            if row['role'] not in {'model', 'manual', 'frozen', 'protected', 'recipe'}:
                continue
            path = ROOT / row['new_path']
            self.assertTrue(path.is_file(), row['new_path'])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row['sha256'], row['new_path'])


if __name__ == '__main__':
    unittest.main()
