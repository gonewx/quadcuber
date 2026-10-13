"""Record an explicitly approved mechanical revision; retain historical frozen provenance."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
G=ROOT/'generated/mechanical'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    changed={}
    for row in json.loads((ROOT/'mechanical/inputs/layout-baseline.json').read_text())['files']:
        if not row['new_path'].startswith(('mechanical/','generated/mechanical/')):continue
        if row['role'] not in {'model','manual','frozen','protected','recipe','inventory'}:continue
        p=ROOT/row['new_path'];digest=sha(p)
        if digest!=row['sha256']:
            assert row['role'] not in {'frozen','protected'},row['new_path']
            assert row['new_path'].startswith(('mechanical/','generated/mechanical/')),row['new_path']
            changed[row['new_path']]=digest
    pdf=G/'manual/manual.pdf';guide=json.loads((G/'manual/guide.json').read_text())
    data=dict(revision='INTEGRATED-GRAVITY-R5-BASE64-2026-10-13',baseline_main='d6bda1d7c7be800161ae366a072e22fdf10a1728',scope='Approved64-new-stock lower-frame integration; heads/support/firmware/electronics unchanged. No physical stiffness or powered acceptance.',models=json.loads((G/'candidate-manifest.json').read_text()),pdf=dict(bytes=pdf.stat().st_size,sha256=sha(pdf),pages=len(guide['steps'])),updated_assets=changed)
    (G/'release.json').write_text(json.dumps(data,indent=2)+'\n')
    print('Recorded',len(changed),'updated mechanical assets;',len(guide['steps']),'pages')
if __name__=='__main__':main()
