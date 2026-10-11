"""Rebuild models and current Site in isolation; fail on any frozen output drift."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


with tempfile.TemporaryDirectory(prefix='quadcuber-rebuild-') as directory:
    target = Path(directory) / 'final'
    shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    before = hashes(target / 'site-source/dist')
    model_before = hashes(target / 'models')
    for script in ['build_candidate.py', 'generate_inventory.py', 'site-source/build_integrated_revision.py']:
        subprocess.run([sys.executable, str(target / script)], cwd=target, check=True, stdout=subprocess.DEVNULL)
    for label, expected, actual in [('models', model_before, hashes(target / 'models')),
                                     ('site', before, hashes(target / 'site-source/dist'))]:
        changed = [p for p in expected.keys() | actual.keys() if expected.get(p) != actual.get(p)]
        if changed:
            raise SystemExit(f'{label} rebuild differs: {changed}')
    print(f'Reproducible: {len(model_before)} models; {len(before)} Site files byte-identical.')
