"""Prevent wrong-part, wrong-side and mixed-version first-board deliveries."""
import csv
import hashlib
import io
import json
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'generated/electronics/engineering-first-board'


class FirstBoardPackage(unittest.TestCase):
    def setUp(self):
        self.assertTrue((OUT / 'manifest.json').exists(), 'Unique first-board package has not been generated')
        self.manifest = json.loads((OUT / 'manifest.json').read_text())

    def rows(self, name):
        with (OUT / name).open(newline='') as f:
            return list(csv.DictReader(f))

    def test_factory_and_hand_solder_partition_preserves_exact_parts(self):
        factory = self.rows('assembly/jlc-smt-bom.csv')
        refs = [r.strip() for g in factory for r in g['Designator'].split(',')]
        hand = self.rows('assembly/hand-solder-purchase.csv')
        handrefs = {r['Reference'] for r in hand}
        source = {r['Reference']: r for r in self.rows('../bom.csv') if int(r['Quantity'])}
        self.assertEqual(len(refs), len(set(refs)))
        self.assertFalse(set(refs) & handrefs)
        self.assertEqual(set(refs) | handrefs, set(source))
        self.assertEqual(handrefs, {'J1','J2','J3','J4','J10','J11','J12','J13',
                                   'J20','J21','J22','J23','C2','C3','C102','C122','C142','C162'})
        self.assertIn('J5', refs, 'USB-C SMT contacts must stay with factory placement')
        self.assertNotIn('C26', refs + list(handrefs))
        self.assertNotIn('C36', refs + list(handrefs))
        for g in factory:
            for r in g['Designator'].split(','):
                self.assertEqual(g['MPN'], source[r.strip()]['MPN'])
        self.assertEqual(next(r for r in hand if r['Reference']=='J1')['MPN'], 'RASPC722X')

    def test_factory_positions_match_original_without_guessing_rotation(self):
        orig = {r['Ref']:r for r in self.rows('../positions.csv')}
        cpl = self.rows('assembly/jlc-smt-cpl.csv')
        bomrefs = {r.strip() for g in self.rows('assembly/jlc-smt-bom.csv') for r in g['Designator'].split(',')}
        self.assertEqual({r['Designator'] for r in cpl}, bomrefs)
        for r in cpl:
            s = orig[r['Designator']]
            self.assertEqual(float(r['Mid X']), float(s['PosX']))
            self.assertEqual(float(r['Mid Y']), float(s['PosY']))
            self.assertEqual(float(r['Rotation']), float(s['Rot']) % 360)
            self.assertEqual(r['Layer'].lower(), s['Side'])
        self.assertEqual(sum(r['Layer']=='Bottom' for r in cpl), 15)

    def test_unique_entry_supersedes_every_old_variant(self):
        old = ROOT / 'generated/electronics/release-preflight'
        for folder in old.glob('ENG-*'):
            self.assertTrue((folder/'SUPERSEDED_NOT_FOR_ORDER.txt').exists(), str(folder))
            manifest = folder/'manifest.json'
            if manifest.exists():
                self.assertEqual(json.loads(manifest.read_text())['status'], 'SUPERSEDED_DO_NOT_USE_FOR_ORDER')
        self.assertIn('engineering-first-board', (ROOT/'electronics/README.md').read_text())
        self.assertIn('engineering-first-board', (ROOT/'README.md').read_text())

    def test_archive_hashes_and_immutable_design_baseline(self):
        for rel, digest in self.manifest['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(), digest, rel)
        for rel in self.manifest['immutable_design_files']:
            self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),
                             self.manifest['design_baseline_sha256'][rel], rel)
        with zipfile.ZipFile(OUT/'quadcuber-A1-first-board-db20b98.zip') as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(set(z.namelist()), set(self.manifest['payload_sha256']) | {'manifest.json'})
            self.assertEqual(json.loads(z.read('manifest.json')), self.manifest)
            for name, digest in self.manifest['payload_sha256'].items():
                self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(), digest, name)
                self.assertEqual(hashlib.sha256((OUT/name).read_bytes()).hexdigest(), digest, name)
            with zipfile.ZipFile(io.BytesIO(z.read('fabrication/gerber-drill-only.zip'))) as g:
                self.assertEqual(sum(n.endswith('.drl') for n in g.namelist()), 2)
                self.assertEqual(len(g.namelist()), 14)  # 11 layers, 2 drills, Gerber job
            self.assertFalse(any('ENG-FULL' in n or 'ENG-POWER-CONTROLLER' in n for n in z.namelist()))


if __name__ == '__main__':
    unittest.main()
