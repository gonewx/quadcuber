"""Independent frozen bytes survive the repository layout migration."""
import hashlib
import json
from pathlib import Path
import unittest
import subprocess
import sys
import tempfile
import os
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]


class RepositoryLayout(unittest.TestCase):
    def test_compatibility_entries_preserve_query_and_step(self):
        names = ['docs/lego/index.html', 'docs/wiring/index.html', 'docs/wiring/direct-breadboard.html']
        names += ['mechanical/final/site-source/dist/' + page for page in
                  ['index.html', 'integrated-assembly.html', 'integrated-operation.html', 'integrated-support.html']]
        for name in names:
            text = (ROOT / name).read_text() if (ROOT / name).exists() else ''
            self.assertIn('location.search', text, name)
            self.assertIn('location.hash', text, name)
            self.assertIn('generated/', text, name)

    def test_deployable_archives_fit_existing_host_limit(self):
        for path in (ROOT / 'dist/site').rglob('*.zip'):
            self.assertLessEqual(path.stat().st_size, 25 * 1024 * 1024, str(path))
        self.assertTrue((ROOT / 'dist/site/integrated/full-revision.zip').is_file())

    def test_wiring_generated_links_resolve(self):
        for page in (ROOT / 'generated/wiring').glob('*.html'):
            text = re.sub(r'<script[\s\S]*?</script>', '', page.read_text())
            for url in re.findall(r'(?:href|src)="([^"]+)"', text):
                if ':' not in url and not url.startswith('#'):
                    self.assertTrue((page.parent / url.split('#')[0]).is_file(), (page.name, url))

    def test_head_validator_retains_frozen_source_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            shutil.copytree(ROOT / 'generated/mechanical/manual', Path(folder) / 'manual')
            result = subprocess.run([sys.executable, str(ROOT / 'mechanical/assembly/validate_final_head.py')],
                                    cwd=folder, env={**os.environ, 'QUADCUBER_MECHANICAL_OUTPUT': folder},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_standalone_perfboard_uses_output_directories(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT / 'wiring', root / 'wiring', ignore=shutil.ignore_patterns('__pycache__'))
            subprocess.run([sys.executable, str(root / 'wiring/perfboard_layout.py')], cwd=folder,
                           check=True, stdout=subprocess.DEVNULL)
            self.assertTrue((root / 'generated/wiring/perfboard-front.svg').is_file())
            self.assertTrue((root / 'docs/perfboard.md').is_file())
            self.assertFalse((root / 'wiring/perfboard-front.svg').exists())
            self.assertFalse((root / 'perfboard.md').exists())

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
        # The layout baseline remains historical. These source files now
        # implement approved R/L selection; behavioral safety tests cover them.
        # R config retains its semantic digest; fixtures, measurements and models retain bytes.
        evolved_firmware = {'firmware/pico/arm_test.py', 'firmware/pico/motor.py',
                            'firmware/pico/encoder.py', 'firmware/pico/config.py'}
        import runpy
        r = runpy.run_path(str(ROOT / 'firmware/pico/config.py'))['ARMS']['R']
        self.assertEqual(hashlib.sha256(json.dumps(r, sort_keys=True,
                         separators=(',', ':')).encode()).hexdigest(),
                         '94e758d94e6b13dd9996fae86726cb6be0f0d906430f62aa862fec98e80dd24a')
        for row in baseline['files']:
            if row['new_path'] in evolved_firmware:
                continue
            if row['role'] not in {'model', 'manual', 'frozen', 'protected', 'recipe', 'inventory'}:
                continue
            path = ROOT / row['new_path']
            self.assertTrue(path.is_file(), row['new_path'])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row['sha256'], row['new_path'])


if __name__ == '__main__':
    unittest.main()
