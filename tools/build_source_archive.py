"""Deterministic source and verified illustration archive; never packages itself."""
from pathlib import Path
import zipfile
ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('mechanical/inputs', 'mechanical/assembly', 'mechanical/parts', 'web', 'generated/mechanical')
FILES = ('tools/build_source_archive.py', 'tools/build_distribution.py',
         'tools/check_rebuild.py', 'README.md', 'LICENSE', 'docs/history.md')

def build(root=ROOT, output=None, *, complete=False):
    root = Path(root)
    output = Path(output) if output else root / 'dist/downloads/full-revision.zip'
    output.parent.mkdir(parents=True, exist_ok=True)
    paths = [p for folder in DIRECTORIES for p in (root / folder).rglob('*')
             if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    paths += [p for p in (root / 'mechanical').iterdir() if p.is_file()]
    paths += [root / name for name in FILES if (root / name).is_file()]
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(paths):
            if not complete and path.suffix.lower() in {'.png', '.pdf'}:
                continue
            info = zipfile.ZipInfo('quadcuber/' + path.relative_to(root).as_posix(), (2026, 10, 11, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    return output

if __name__ == '__main__':
    print(build())
