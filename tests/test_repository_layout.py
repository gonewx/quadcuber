"""Independent frozen bytes survive the repository layout migration."""
import hashlib
import json
from pathlib import Path
import unittest
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


class RepositoryLayout(unittest.TestCase):
    def test_canonical_dynamic_step_images_resolve(self):
        page = ROOT / 'generated/site/integrated-assembly.html'
        data = json.JSONDecoder().raw_decode(page.read_text().split('window.WORKBENCH_DATA=', 1)[1])[0]
        for step in data['guide']['steps']:
            self.assertTrue((page.parent / data['imageRoot'] / step['image']).is_file(), step['image'])

    def test_distribution_builds_in_empty_output(self):
        builder = ROOT / 'tools/build_distribution.py'
        self.assertTrue(builder.is_file(), 'distribution must be built from repository sources')
        with tempfile.TemporaryDirectory() as folder:
            subprocess.run([sys.executable, str(builder), '--output', folder], cwd=folder, check=True,
                           stdout=subprocess.DEVNULL)
            for name in ['site/index.html', 'site/integrated-operation.html',
                         'offline/assembly.html', 'offline/operation.html', 'downloads/full-revision.zip']:
                self.assertTrue((Path(folder) / name).is_file(), name)

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
