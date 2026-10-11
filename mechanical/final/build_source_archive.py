"""Deterministic compact source download; no deployment and no recursive archives."""
from pathlib import Path
import zipfile


def build(root):
    root = Path(root)
    output = root / 'site-source/dist/integrated/full-revision.zip'
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for file in sorted(root.rglob('*')):
            relative = file.relative_to(root)
            if not file.is_file() or any(p in {'dist', 'offline-viewer', '__pycache__', '.git'} for p in relative.parts):
                continue
            if file.suffix.lower() in {'.png', '.pdf', '.pyc', '.zip'}:
                continue
            entry = zipfile.ZipInfo('quadcuber-final/' + relative.as_posix(), date_time=(2026, 10, 9, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, file.read_bytes(), compresslevel=9)
    return output


if __name__ == '__main__':
    print(build(Path(__file__).resolve().parent))
