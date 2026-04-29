"""新聞看板本機伺服器：提供 dashboard 與 /api/refresh 即時抓取端點。

執行：python src/serve.py
然後瀏覽器會自動開啟 http://localhost:8765/index.html
右下角的「立即更新」按鈕才能用。
"""
import sys
import json
import subprocess
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

PORT = 8765
ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = ROOT / "dashboard"
SRC_DIR = ROOT / "src"

_refresh_lock = threading.Lock()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def log_message(self, fmt, *args):
        # 只 log 重要的，避免太雜
        if "/api/" in args[0] if args else "":
            super().log_message(fmt, *args)

    def _json(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path == "/api/refresh":
            if not _refresh_lock.acquire(blocking=False):
                return self._json(429, {"ok": False, "error": "另一個更新正在進行中"})
            try:
                print("\n[refresh] 收到立即更新請求...")
                proc = subprocess.run(
                    [sys.executable, str(SRC_DIR / "run_all.py")],
                    capture_output=True, text=True, encoding="utf-8", errors="replace"
                )
                ok = proc.returncode == 0
                # 從 stdout 找重點摘要
                summary = ""
                for line in proc.stdout.splitlines():
                    if "articles" in line and "→" in line:
                        summary = line.strip().split("Done.")[-1].strip().split("→")[0].strip()
                        break
                print(f"[refresh] 完成，returncode={proc.returncode}")
                self._json(200, {"ok": ok, "summary": summary, "stdout_tail": proc.stdout[-500:]})
            except Exception as exc:
                print(f"[refresh] 例外: {exc}")
                self._json(500, {"ok": False, "error": str(exc)})
            finally:
                _refresh_lock.release()
        else:
            self._json(404, {"ok": False, "error": "Not found"})

    def do_GET(self):
        # 預設首頁導向 index.html
        if self.path in ("/", ""):
            self.path = "/index.html"
        return super().do_GET()


def main():
    if not (DASHBOARD_DIR / "index.html").exists():
        print(f"⚠ 找不到 {DASHBOARD_DIR / 'index.html'}")
        print("請先執行：python src/run_all.py")
        sys.exit(1)

    url = f"http://localhost:{PORT}/index.html"
    print("=" * 60)
    print("新聞看板 — 本機伺服器")
    print("=" * 60)
    print(f"Dashboard: {url}")
    print(f"按 Ctrl+C 停止")
    print("=" * 60)

    # 1.2 秒後自動開啟瀏覽器（讓伺服器先啟動）
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    with ThreadingHTTPServer(("127.0.0.1", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n伺服器已停止。")


if __name__ == "__main__":
    main()
