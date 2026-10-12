"""Configurable KiCad CLI and pcbnew interpreter; never silently use KiCad 9."""
import json
import os
from pathlib import Path
import shlex
import sys

EXPECTED_VERSION = json.loads(Path(__file__).with_suffix('.json').read_text())['kicad']


def cli_command():
    if os.environ.get('KICAD_CLI'):
        return [os.environ['KICAD_CLI']]
    if os.environ.get('KICAD_APP_RUN'):
        return [os.environ['KICAD_APP_RUN'], 'kicad-cli']
    return ['kicad-cli']


def python_command():
    if os.environ.get('KICAD_PYTHON'):
        return shlex.split(os.environ['KICAD_PYTHON'])
    if os.environ.get('KICAD_APP_RUN'):
        return [os.environ['KICAD_APP_RUN'], 'python3.11']
    return [sys.executable]


def require_version(version):
    if version != EXPECTED_VERSION:
        raise RuntimeError(f'KiCad {EXPECTED_VERSION} required, got {version!r}; '
                           'configure KICAD_CLI and KICAD_PYTHON, or KICAD_APP_RUN')
