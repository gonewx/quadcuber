"""Translate URLs between canonical and distributable pages."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def mapping():
    result = {'integrated/manifest.json': '../mechanical/candidate-manifest.json',
              'integrated/assembly.json': '../mechanical/assembly-integrated132.json',
              'integrated/operation-guide.json': 'operation-guide.json',
              'integrated/full-revision.zip': '../../dist/downloads/full-revision.zip'}
    for path in (ROOT / 'generated/mechanical').rglob('*'):
        if path.is_file():
            relative = path.relative_to(ROOT / 'generated/mechanical').as_posix()
            result['integrated/' + relative.removeprefix('manual/')] = '../mechanical/' + relative
    return result

def translate(text, pairs):
    for old, new in sorted(pairs.items(), key=lambda item: -len(item[0])):
        text = text.replace(old, new)
    return text

def canonicalize(text):
    return translate(text, mapping()).replace('"imageRoot":"integrated/"', '"imageRoot":"../mechanical/manual/"')

def publicize(text):
    return translate(text, {v: k for k, v in mapping().items()}).replace('"imageRoot":"../mechanical/manual/"', '"imageRoot":"integrated/"')
