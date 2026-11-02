# -*- coding: utf-8 -*-
"""
小鲸鱼打工日记 —— 本地小服务器（只用 Python 标准库，不用装任何东西）

用法：
    python server.py              起服务并自动打开浏览器
    python server.py --no-browser 只起服务，不自动开浏览器
    python server.py --port 9000  指定起始端口

它会：
    * 把同目录的 index.html 当首页
    * GET  /api/quote  随机吐一句打工语录
    * GET  /api/state  读回上次存的打卡数据（同目录 data.json）
    * POST /api/state  把页面上的打卡数据写进 data.json

Ctrl+C 结束。
"""

import json
import random
import socket
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data.json"

QUOTES = [
    "打工是不会打工的…但工资是真的香。",
    "今天也很努力地在努力摸鱼，辛苦了。",
    "海很大，我的工时也很大。",
    "老板说要有光，于是我开了加班的灯。",
    "我不是懒，我只是在保存体力等下班。",
    "摸鱼五分钟，回血两小时。",
    "会议的本质是把一个人的事变成十个人的事。",
    "我这条鲸鱼，搁浅在了下午四点。",
    "努力工作，是为了以后能体面地摆烂。",
    "深海里没有信号，所以别 @ 我。",
    "工资到账的那一刻，我又可以了。",
    "摸鱼不是偷懒，是给灵魂换水。",
    "别急，慢一点也能游到。",
    "把事做完的那一刻，鲸鱼会喷一次水。",
]


def read_state():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def write_state(obj):
    DATA_FILE.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


class Handler(SimpleHTTPRequestHandler):
    server_version = "WhaleDiary/1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    # 安静一点，只打一行
    def log_message(self, fmt, *args):
        try:
            sys.stdout.write("  " + (fmt % args) + "\n")
        except Exception:
            pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def _send_json(self, payload, code=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/quote":
            return self._send_json({"quote": random.choice(QUOTES)})
        if path == "/api/state":
            return self._send_json(read_state())
        if path in ("/", ""):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b""

        if path == "/api/state":
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except Exception:
                return self._send_json({"ok": False, "error": "bad json"}, 400)
            if not isinstance(payload, dict):
                return self._send_json({"ok": False, "error": "expect object"}, 400)
            write_state(payload)
            return self._send_json({"ok": True, "file": str(DATA_FILE)})

        return self._send_json({"ok": False, "error": "not found"}, 404)


def pick_port(start=8848, tries=30):
    for port in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise SystemExit("8848 往后 30 个端口都被占了，先关掉点东西再试。")


def main():
    args = sys.argv[1:]
    start = 8848
    if "--port" in args:
        try:
            start = int(args[args.index("--port") + 1])
        except (IndexError, ValueError):
            pass

    if not (ROOT / "index.html").exists():
        raise SystemExit("同目录找不到 index.html，先把它和 server.py 放在一起。")

    port = pick_port(start)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = "http://127.0.0.1:{0}/".format(port)

    print("")
    print("  🐋  小鲸鱼打工日记已开张")
    print("  ---------------------------------------")
    print("  地址： " + url)
    print("  目录： " + str(ROOT))
    print("  数据： " + str(DATA_FILE))
    print("  停止： 按 Ctrl + C")
    print("  ---------------------------------------")
    print("")

    if "--no-browser" not in args:
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  收工，明天再战。")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
