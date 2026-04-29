"""一次跑完所有抓取任務。"""
import sys
import subprocess
import time
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
SCRIPTS = ["fetch_news.py", "fetch_crypto.py", "fetch_market.py", "fetch_reports.py", "build_dashboard.py"]


def main():
    start = time.time()
    print("=" * 60)
    print("新聞看板 — 全資料抓取")
    print("=" * 60)
    failed = []
    for s in SCRIPTS:
        print(f"\n>>> {s}")
        rc = subprocess.call([sys.executable, str(HERE / s)])
        if rc != 0:
            failed.append(s)
            print(f"   ⚠ {s} 失敗 (exit {rc})")
    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    if failed:
        print(f"完成（{len(failed)} 個失敗）：{failed}")
    else:
        print(f"全部完成 ✓ 耗時 {elapsed:.1f} 秒")
    print("=" * 60)
    print("\n下一步：用 Chrome 打開 dashboard\\index.html")


if __name__ == "__main__":
    main()
