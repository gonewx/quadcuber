from pathlib import Path
import hashlib, html, json, re, shutil

root = Path(__file__).resolve().parent
source = root.parent / 'lift-feasibility/pose-coupled-support-review/complete-seat-review/operation-guide132'
raw = (source / 'operation-guide132.json').read_bytes()
guide = json.loads(raw)
assert guide['review_only'] is True
assert guide['world_axes'] == {'R': [550, 0, 0], 'L': [-550, 0, 0], 'F': [0, 0, 550], 'B': [0, 0, -550]}
state_checks = {}
for key, state in guide['states'].items():
    path = (source / state['file']).resolve()
    assert path.is_relative_to(source.resolve()), 'State path outside operation sources'
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == state['sha256'], key
    text = data.decode()
    rows = [line for line in text.split('\n0 FILE ')[0].splitlines() if line.startswith('1 ')]
    assert len(rows) == state['count'] and state['count'] in [899, 897], key
    state['model_text'] = text
    assert state.get('cube_orientation', 'axis_aligned') == 'axis_aligned'
    state_checks[key] = {'count': state['count'], 'sha256': state['sha256'], 'file': state['file']}

image_checks = {}
def image_file(filename):
    path = (source / filename).resolve()
    assert path.is_relative_to(source.resolve()) and path.is_file(), filename
    target = Path('operation132') / path.relative_to(source.resolve())
    (root / 'dist' / target).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, root / 'dist' / target)
    image_checks[str(target)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return str(target)

ids = set()
for state in guide['states'].values():
    if state.get('diagram_file'):
        state['diagram_file'] = image_file(state['diagram_file'])
for stage in guide['stages']:
    assert stage['id'] not in ids
    ids.add(stage['id'])
    assert stage['state_id'] in guide['states']
    assert stage['action_type'] in ['manual', 'motor_design', 'check']
    assert stage['instructions_zh'] and isinstance(stage['cautions_zh'], list)
    if stage.get('diagram_file'):
        stage['diagram_file'] = image_file(stage['diagram_file'])

def list_html(items):
    return '<ul>' + ''.join('<li>' + html.escape(item) + '</li>' for item in items) + '</ul>'

angle_diagram = image_file('diagrams/angle-reference.png')
relationships = list_html(guide.get('relationship_zh', []))
relationships += '<h3>机械头角度怎么看</h3><p>正对同一个机械头：0°夹指一上一下；50°斜置，留出装料通道；90°夹指左右横置。三个示例均保持夹口张开。角度描述整个机械头的转角，不是舵机夹紧角度。</p><figure><a href="' + angle_diagram + '" target="_blank" rel="noopener"><img src="' + angle_diagram + '" alt="同一原机械头在0、50和90度的实际模型朝向对照" loading="lazy"></a><figcaption>点击看原图。转头之前，先确认该头已张开；另一对夹头或锁定托座必须可靠支撑魔方。仅供设计审阅。</figcaption></figure>' 
if guide.get('relationship_diagram_file'):
    diagram = image_file(guide['relationship_diagram_file'])
    relationships += '<figure><img src="' + html.escape(diagram, quote=True) + '" alt="新支承与原四臂的整机关系图" loading="lazy"><figcaption>' + html.escape(guide.get('relationship_diagram_caption_zh', '整机关系图；世界方向与上方3D一致')) + '</figcaption></figure>'
body = (root / 'operation-guide.html').read_text().replace('RELATIONSHIP_CONTENT', relationships).replace('WARNING_CONTENT', list_html(guide.get('warnings_zh', [])))
nav = '<nav class="review-tabs" aria-label="模型与实测记录"><a href="index.html">新支承候选审阅</a><a href="operation-guide.html" aria-current="page">整机关系与放入／退出</a><a href="history-219.html">219版失败记录／旧说明</a></nav>'
candidate = (root / 'dist/index.html').read_text()
large = next(script for script in re.findall(r'<script>([\s\S]*?)</script>', candidate) if 'const THREE = ' in script)
library = large[:large.index('try{\nconst box=')]
favicon = re.search(r'<link rel="icon"[^>]+>', candidate).group()
head = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: 'self'; connect-src 'none'; base-uri 'none'; form-action 'none'"><title>整机关系与放入／退出 · 132件设计审阅</title><meta name="description" content="132件新支承与原四臂的关系、魔方放入和退出、夹持交接与40毫米托座位移。仅供设计审阅，未经实物验证。">'''
def encode(value):
    return json.dumps(value, ensure_ascii=False).replace('<', '\\u003c')
data_script = 'window.OPERATION_GUIDE=' + encode(guide) + ';window.CANDIDATE_COLOR_META=' + encode((root / 'candidate-colors.ldr').read_text()) + ';'
scripts = [data_script, (root / 'candidate-source-adapter.js').read_text() + (root / 'operation-guide-core.js').read_text(), library + (root / 'operation-viewer-app.js').read_text(), (root / 'operation-guide-ui.js').read_text()]
output = head + favicon + '<style>' + (root / 'operation-guide.css').read_text() + '</style></head><body>' + nav + body + ''.join('<script>' + script + '</script>' for script in scripts) + '</body></html>'
(root / 'dist/operation-guide.html').write_text(output)
manifest = {'source_sha256': hashlib.sha256(raw).hexdigest(), 'route': 'operation-guide.html', 'stage_count': len(guide['stages']), 'states': state_checks, 'diagrams': image_checks, 'review_only': True, 'reference_cube_mm': 56, 'reference_cube_in_lego_count': False}
(root / 'operation-guide132-source.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'operationGuideBytes': len(output.encode()), 'stages': len(guide['stages']), 'states': {k: v['count'] for k, v in guide['states'].items()}, 'review_only': True}))
