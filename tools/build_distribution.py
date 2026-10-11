"""Assemble public, offline and download layouts from canonical repository outputs."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'web'))
from resource_paths import publicize
from build_source_archive import build as archive_sources
PAGES = ('index.html', 'integrated-assembly.html', 'integrated-operation.html', 'integrated-support.html')

def build(output):
    output = Path(output).resolve()
    subprocess.run([sys.executable, str(ROOT / 'web/build_integrated_revision.py')], check=True)
    site = output / 'site'
    resources = site / 'integrated'
    resources.mkdir(parents=True, exist_ok=True)
    mechanical = ROOT / 'generated/mechanical'
    for path in mechanical.rglob('*'):
        if not path.is_file():
            continue
        relative = path.relative_to(mechanical).as_posix().removeprefix('manual/')
        target = resources / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    for src, dst in [('candidate-manifest.json', 'manifest.json'), ('assembly-integrated132.json', 'assembly.json')]:
        shutil.copyfile(mechanical / src, resources / dst)
    for name in PAGES:
        (site / name).write_text(publicize((ROOT / 'generated/site' / name).read_text()))
    (resources / 'operation-guide.json').write_text(publicize((ROOT / 'generated/site/operation-guide.json').read_text()))
    archive = archive_sources(ROOT, output / 'downloads/full-revision.zip')
    shutil.copyfile(archive, resources / 'full-revision.zip')
    offline = output / 'offline'
    shutil.copytree(site, offline, dirs_exist_ok=True)
    names = dict(zip(PAGES, ('index.html', 'assembly.html', 'operation.html', 'support.html')))
    for src, dst in names.items():
        text = (site / src).read_text()
        for old, new in names.items():
            text = text.replace(old, new)
        (offline / dst).write_text(text)
        if src != dst:
            (offline / src).unlink(missing_ok=True)
    print('Built four public pages, four offline pages and independently buildable source archive.')
    return output

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    build(parser.parse_args().output)
