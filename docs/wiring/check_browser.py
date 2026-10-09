"""浏览器验收与 PNG 导出（可选依赖 playwright + Chromium，不影响标准库构建）。

python docs/wiring/check_browser.py --export-png --screenshots /tmp/wiring-review
"""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import struct
from threading import Thread

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def check(page, mode, group):
    """检查用户可见内容与实际下载，而不只检查 JS 内部状态。"""
    page.locator(f'[data-mode="{mode}"]').click()
    page.locator(f'[data-filter="{group}"]').click()
    prefix = 'direct-breadboard' + ('-rl' if mode == 'RL' else '')
    net = json.loads((HERE / (prefix + '-netlist.json')).read_text())
    wires = [w['code'] for w in net['wires']]
    resistors = [r[0] for r in net['resistors']]
    assert page.locator('.canvas svg:visible').count() == 1
    assert page.locator('.canvas svg:visible [data-wire]').evaluate_all(
        '(xs)=>xs.map(x=>x.dataset.wire)') == wires
    assert page.locator('tbody:visible tr td:first-child').all_text_contents() == wires + resistors
    assert page.locator('[data-mode][aria-pressed="true"]').get_attribute('data-mode') == mode
    assert page.locator('[data-filter][aria-pressed="true"]').get_attribute('data-filter') == group
    for selector, faded in [('.canvas svg:visible [data-group]', '0.1'), ('tbody:visible tr[data-group]', '0.3')]:
        for item in page.locator(selector).evaluate_all(
                '(xs)=>xs.map(x=>({group:x.dataset.group,opacity:x.style.opacity}))'):
            assert item['opacity'] == ('1' if group == 'all' or item['group'] == group else faded)
    assert page.locator('tbody:visible tr[data-added="true"]').count() == (17 if mode == 'RL' else 0)
    for link in page.locator('[data-download]').all():
        href = link.get_attribute('href')
        assert href.startswith(prefix + '.') or href == prefix + '-netlist.json'
        result = page.request.get('http://' + page.url.split('/')[2] + '/docs/wiring/' + href)
        assert result.ok, href
        assert ('R+L' in link.inner_text()) == (mode == 'RL')
    assert page.locator('#complete-wiring').count() == 1
    visible = page.locator('body').inner_text()
    if mode == 'RL':
        for phrase in ['用户尚未确认', 'ARM_ID', '不切换 GPIO', '不能保证 L 输入为低', '电流、温升']:
            assert phrase in visible, phrase
        assert 'import arm_test' not in visible
    else:
        assert 'import arm_test' in visible
        assert '新增 L：' not in visible
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), '页面横向溢出'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export-png', action='store_true')
    parser.add_argument('--screenshots', type=Path)
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright

    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    url = f'http://127.0.0.1:{server.server_port}/docs/wiring/'
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
            # 从独立 SVG 原尺寸导出；不把页面的筛选/缩放状态烘焙进下载图。
            for stem, height in [('direct-breadboard', 1430), ('direct-breadboard-rl', 2020)]:
                page = browser.new_page(viewport={'width': 2200, 'height': height}, device_scale_factor=1)
                page.goto(url + stem + '.svg')
                page.evaluate('document.fonts.ready')
                if args.export_png:
                    page.locator('svg').screenshot(path=str(HERE / (stem + '.png')))
                png = (HERE / (stem + '.png')).read_bytes()
                assert png[:8] == b'\x89PNG\r\n\x1a\n'
                assert struct.unpack('>II', png[16:24]) == (2200, height)
                page.close()
            for name, viewport in [('desktop', {'width': 1440, 'height': 1000}),
                                   ('mobile', {'width': 390, 'height': 844})]:
                page = browser.new_page(viewport=viewport, is_mobile=name == 'mobile', has_touch=name == 'mobile')
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(url + 'direct-breadboard.html#complete-wiring')
                assert page.locator('[data-mode="R"]').get_attribute('aria-pressed') == 'true'
                # 每种筛选下往返切换，确认筛选保持有效。
                for group in ('all', 'power', 'ground', 'control', 'encoder', 'motor', 'servo'):
                    for mode in ('RL', 'R', 'RL', 'R'):
                        check(page, mode, group)
                        page.locator(f'[data-mode="{"RL" if mode == "R" else "R"}"]').click()
                        assert page.locator('[data-filter][aria-pressed="true"]').get_attribute('data-filter') == group
                for mode in ('R', 'RL'):
                    check(page, mode, 'all')
                    if name == 'mobile':
                        assert page.locator('.canvas').evaluate('(x)=>x.scrollWidth>x.clientWidth')
                        page.locator('.canvas').evaluate('(x)=>x.scrollLeft=300')
                        assert page.locator('.canvas').evaluate('(x)=>x.scrollLeft') > 0
                        page.locator('.canvas').evaluate('(x)=>x.scrollLeft=0')
                    if args.screenshots:
                        args.screenshots.mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(args.screenshots / f'{name}-{mode}.png'), full_page=True)
                page.emulate_media(media='print')
                assert page.locator('.canvas svg:visible').count() == 1
                assert not errors, errors
                page.close()
                print(f'{name}: 28轮模式/筛选检查、下载、横向滚动、打印通过，无 JS 错误')
            # 禁用 JS 时保留安全的原 R 页面；不展示第二套表/图。
            page = browser.new_page(java_script_enabled=False)
            page.goto(url + 'direct-breadboard.html')
            assert page.locator('.canvas svg:visible [data-wire]').count() == 25
            assert page.locator('tbody:visible tr').count() == 29
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


if __name__ == '__main__':
    main()
