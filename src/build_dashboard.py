"""把 data/*.json 嵌入 dashboard/index.html (避免 file:// CORS)。"""
import sys
import json
import datetime as dt
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TEMPLATE = ROOT / "dashboard" / "template.html"
OUTPUT = ROOT / "dashboard" / "index.html"


def load_json(name: str):
    p = DATA_DIR / name
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    print("Building dashboard...")
    news = load_json("news.json")
    crypto = load_json("crypto.json")
    market = load_json("market.json")
    reports = load_json("reports.json")
    intel = load_json("intel.json")

    template = TEMPLATE.read_text(encoding="utf-8")
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
    built_at = now.strftime("%Y-%m-%d %H:%M")

    html = (template
        .replace("/*__NEWS_DATA__*/null", json.dumps(news, ensure_ascii=False))
        .replace("/*__CRYPTO_DATA__*/null", json.dumps(crypto, ensure_ascii=False))
        .replace("/*__MARKET_DATA__*/null", json.dumps(market, ensure_ascii=False))
        .replace("/*__REPORTS_DATA__*/null", json.dumps(reports, ensure_ascii=False))
        .replace("/*__INTEL_DATA__*/null", json.dumps(intel, ensure_ascii=False))
        .replace("__BUILT_AT__", built_at)
    )
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Done → {OUTPUT}")
    print(f"Built at {built_at} (TPE)")


if __name__ == "__main__":
    main()
