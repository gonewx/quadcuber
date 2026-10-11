"""Frozen final assembly, resource and inventory contract (no hardware claims)."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1] / 'mechanical/final'


def read_json(path):
    return json.loads((ROOT / path).read_text())


def subfiles(text):
    return {b.splitlines()[0].lower(): b.splitlines()[1:]
            for b in text.split('0 FILE ')[1:]}


class FinalMechanics(unittest.TestCase):
    def test_frozen_inputs_models_and_published_copies(self):
        for name, digest in read_json('frozen-source-sha256.json').items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest, name)
        frozen = read_json('PROVENANCE.json')['frozen_models']
        self.assertEqual(read_json('candidate-manifest.json'), frozen)
        self.assertEqual(read_json('site-source/dist/integrated/manifest.json'), frozen)
        for row in frozen.values():
            data = (ROOT / row['file']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])
            self.assertEqual(data, (ROOT / 'site-source/dist/integrated' / row['file']).read_bytes())

    def test_all_native_model_dependencies_are_embedded(self):
        for row in read_json('candidate-manifest.json').values():
            files = subfiles((ROOT / row['file']).read_text())
            for lines in files.values():
                for line in lines:
                    fields = line.split()
                    if fields and fields[0] == '1':
                        name = ' '.join(fields[14:]).replace('\\', '/').lower()
                        self.assertTrue(any(k in files for k in [name, 'p/'+name, 'parts/'+name, 's/'+name]), name)

    def test_bom_matches_all_seven_whole_machine_states(self):
        with (ROOT / 'final-BOM.csv').open() as stream:
            bom = collections.Counter({r['part']: int(r['quantity']) for r in csv.DictReader(stream)})
        self.assertEqual(sum(bom.values()), 882)
        whole = [r for r in read_json('candidate-manifest.json').values() if r['parts'] == 882]
        self.assertEqual(len(whole), 7)
        for row in whole:
            files = subfiles((ROOT / row['file']).read_text())
            parts = collections.Counter(line.split()[14] for line in next(iter(files.values())) if line.startswith('1 '))
            self.assertEqual(parts, bom)

    def test_thin_beams_have_axle_holes(self):
        files = subfiles((ROOT / 'models/loading-all50.mpd').read_text())
        root = next(iter(files.values()))
        used = {line.split()[14] for line in root if line.startswith('1 ')}
        self.assertNotIn('32017.dat', used)
        thin = {n for n in used if re.search(r'Beam.*x\s+0\.5', '\n'.join(files[n][:2]))}
        self.assertEqual(thin, {'11478.dat', '32449.dat', '41677.dat'})
        for name in thin:
            self.assertIn('axlehol', '\n'.join(files[name]).lower(), name)

    def test_501_steps_cover_882_instances_once(self):
        guide = read_json('manual/guide.json')
        self.assertEqual(len(guide['steps']), 501)
        self.assertEqual(len({r['instance_key'] for r in guide['instance_introduction_ledger']}), 882)
        self.assertEqual(len(guide['instance_introduction_ledger']), 882)
        c = guide['coverage']
        self.assertEqual((c['base_parts'], c['final_arm_parts'], c['support_parts']), (64, 668, 150))
        self.assertEqual((c['seat_guide_parts'], c['lever_parts']), (130, 20))
        self.assertEqual(c['prebuilt_core_total_parts'], 0)
        self.assertEqual(c['head_steps_per_arm'], 88)
        self.assertEqual(guide, read_json('site-source/dist/integrated/guide.json'))
        for step in guide['steps']:
            image = ROOT / 'manual' / step['image']
            self.assertTrue(image.is_file(), str(image))
            self.assertEqual(image.read_bytes(), (ROOT / 'site-source/dist/integrated' / step['image']).read_bytes())

    def test_pdf_matches_verified_library_delivery(self):
        ref = read_json('PROVENANCE.json')['library']['pdf']
        for name in ['manual/manual.pdf', 'site-source/dist/integrated/manual.pdf']:
            data = (ROOT / name).read_bytes()
            self.assertEqual(len(data), ref['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), ref['sha256'])

    def test_current_routes_have_no_broken_local_links(self):
        for folder, pages in [('site-source/dist', ['index.html', 'integrated-assembly.html', 'integrated-operation.html', 'integrated-support.html']),
                              ('offline-viewer', ['index.html', 'assembly.html', 'operation.html', 'support.html'])]:
            for name in pages:
                page = ROOT / folder / name
                if not page.exists():
                    self.fail(str(page))
                # Script payloads contain historical templates; inspect rendered HTML only.
                html = re.sub(r'<script[\s\S]*?</script>', '', page.read_text())
                for url in re.findall(r'(?:href|src)="([^"]+)"', html):
                    if ':' in url or url.startswith('#'):
                        continue
                    self.assertTrue((page.parent / url.split('#')[0]).is_file(), (name, url))

    def test_compact_download_contains_current_rebuild_inputs(self):
        with zipfile.ZipFile(ROOT / 'site-source/dist/integrated/full-revision.zip') as archive:
            for name in ['candidate.py', 'build_candidate.py', 'build_source_archive.py',
                         'source/baseline-machine-899.mpd', 'source/github-current-model.py',
                         'source/asset-order.json', 'site-source/build_integrated_revision.py',
                         'site-source/build_viewer_workbench.py']:
                self.assertEqual(archive.read('quadcuber-final/' + name), (ROOT / name).read_bytes(), name)

    def test_current_scope_has_no_prebuilt_arm_claim(self):
        for folder, pages in [('site-source/dist', ['index.html', 'integrated-assembly.html', 'integrated-operation.html']),
                              ('offline-viewer', ['index.html', 'assembly.html', 'operation.html'])]:
            for name in pages:
                html = re.sub(r'<script[\s\S]*?</script>', '', (ROOT / folder / name).read_text())
                self.assertNotIn('本册不含这些', html)
                self.assertIn('882', html)


if __name__ == '__main__':
    unittest.main()
