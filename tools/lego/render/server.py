"""本地 HTTP 服务: 给浏览器里的 LDrawLoader 提供零件文件 (自定义零件优先, 其余取自零件库镜像并缓存)。

    python server.py [端口]      默认 8765
"""

import http.server
import os
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import ldraw  # noqa: E402


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=HERE, **k)

    def log_message(self, *a):
        pass

    def do_GET(self):
        path = urllib.parse.unquote(self.path.split("?")[0])
        if not path.startswith("/ldraw/"):
            return super().do_GET()
        rel = path[len("/ldraw/"):]
        data = None
        base = rel.split("/")[-1].lower()
        custom = os.path.join(ldraw.CUSTOM, base)
        if rel.lower() in (base, "parts/" + base) and os.path.exists(custom):
            with open(custom, "rb") as f:
                data = f.read()
        elif rel.startswith("colors/"):
            data = ldraw.fetch_rel(rel)
        else:
            data = ldraw.fetch_rel("complete/ldraw/" + rel.lower())
        if data is None:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
