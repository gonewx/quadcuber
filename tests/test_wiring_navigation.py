"""Current wiring navigation must not send readers to the historical single-arm overview."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'generated/wiring/direct-breadboard.html'


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.href = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href = dict(attrs).get('href')

    def handle_data(self, data):
        if self.href:
            self.links.append((data, self.href))

    def handle_endtag(self, tag):
        if tag == 'a':
            self.href = None


class WiringNavigationTests(unittest.TestCase):
    def test_current_document_links_resolve_to_canonical_reader(self):
        for name in ('README.md', 'docs/single_arm.md', 'docs/wiring/README.md', 'docs/perfboard.md'):
            with self.subTest(name=name):
                path = ROOT / name
                links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', path.read_text())
                current = [(label, href) for label, href in links if '当前接线' in label]
                self.assertTrue(current, name)
                for label, href in current:
                    self.assertEqual((path.parent / href.split('#')[0]).resolve(), TARGET)
                    self.assertIn('R+L', label)

    def test_generated_legacy_pages_label_scope_and_link_current_reader(self):
        for name, scope in (('index.html', '历史单臂'), ('perfboard.html', '可选单臂')):
            with self.subTest(name=name):
                text = (ROOT / 'generated/wiring' / name).read_text()
                self.assertIn(scope, re.search(r'<title>(.*?)</title>', text).group(1))
                current = [(label, href) for label, href in Links(text).links if '当前接线' in label]
                self.assertTrue(current)
                self.assertTrue(all(href == 'direct-breadboard.html' and 'R+L' in label for label, href in current))

    def test_single_arm_doc_distinguishes_historical_mechanics(self):
        text = (ROOT / 'docs/single_arm.md').read_text()
        self.assertIn('历史 v4', text.splitlines()[0])
        self.assertNotIn('docs/wiring/spec.py', text)
        self.assertNotIn('当前机械基线是 v4', text)
        self.assertNotIn('当前 v4', text)
        self.assertNotIn('[最新修改说明]', text)
        self.assertIn('../generated/site/integrated-assembly.html', text)
        self.assertIn('`wiring/spec.py`', text)
