"""Check clean model/page rebuild and a separately extracted source archive."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import tempfile
import zipfile
from build_source_archive import DIRECTORIES, FILES
ROOT = Path(__file__).resolve().parents[1]

def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}

def run(root, script, *args):
    subprocess.run([sys.executable, str(root / script), *args], cwd=root.parent,
                   check=True, stdout=subprocess.DEVNULL)

def verify(root, expected_models, expected_pages):
    shutil.rmtree(root / 'generated/mechanical/models', ignore_errors=True)
    shutil.rmtree(root / 'generated/site', ignore_errors=True)
    run(root, 'mechanical/build_candidate.py')
    run(root, 'mechanical/generate_inventory.py')
    run(root, 'web/build_integrated_revision.py')
    assert hashes(root / 'generated/mechanical/models') == expected_models, 'model drift'
    assert hashes(root / 'generated/site') == expected_pages, 'canonical page drift'

def main():
    expected_models = hashes(ROOT / 'generated/mechanical/models')
    expected_pages = hashes(ROOT / 'generated/site')
    with tempfile.TemporaryDirectory(prefix='quadcuber-rebuild-') as folder:
        target = Path(folder) / 'repository'
        for name in DIRECTORIES:
            shutil.copytree(ROOT / name, target / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for file in list((ROOT / 'mechanical').glob('*')) + [ROOT / name for name in FILES]:
            if file.is_file():
                dest = target / file.relative_to(ROOT)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(file, dest)
        verify(target, expected_models, expected_pages)
        run(target, 'tools/build_distribution.py')
        extracted = Path(folder) / 'extracted'
        with zipfile.ZipFile(target / 'dist/downloads/quadcuber-source-complete.zip') as archive:
            archive.extractall(extracted)
        verify(extracted / 'quadcuber', expected_models, expected_pages)
        compact = Path(folder) / 'compact'
        with zipfile.ZipFile(target / 'dist/downloads/full-revision.zip') as archive:
            archive.extractall(compact)
        compact_root = compact / 'quadcuber'
        shutil.rmtree(compact_root / 'generated/mechanical/models')
        run(compact_root, 'mechanical/build_candidate.py')
        run(compact_root, 'mechanical/generate_inventory.py')
        assert hashes(compact_root / 'generated/mechanical/models') == expected_models
    print(f'PASS: {len(expected_models)} byte-identical models; {len(expected_pages)} canonical outputs rebuilt from empty output directories; complete archive independently rebuilt; compact archive reproduces frozen models.')

if __name__ == '__main__':
    main()
