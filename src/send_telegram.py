"""產生今日 Daily Brief 並推送到 Telegram。"""
import os
import sys
import json
import datetime as dt
from pathlib import Path
from urllib.parse import urlencode
import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DASHBOARD_URL = "https://winnie3721.github.io/news-dashboard/"

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def load(name):
    p = DATA_DIR / name
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def diversify(items, max_per_source=2):
    """Round-robin pull by source so top items don't all come from one outlet."""
    by = {}
    for it in items:
        by.setdefault(it["source"], []).append(it)
    for s in by:
        by[s].sort(key=lambda x: x.get("published", ""), reverse=True)
    out, idx = [], {s: 0 for s in by}
    for _ in range(max_per_source):
        added = False
        for s in by:
            if idx[s] < min(len(by[s]), max_per_source):
                out.append(by[s][idx[s]])
                idx[s] += 1
                added = True
        if not added:
            break
    return out


def short(t, limit=70):
    t = (t or "").strip()
    return t if len(t) <= limit else t[:limit - 1] + "…"


def html_escape(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt_pct(p):
    if p is None:
        return ""
    sign = "+" if p >= 0 else ""
    return f"{sign}{p:.2f}%"


def build_brief() -> str:
    news = load("news.json").get("categories", {})
    crypto = load("crypto.json")
    market = load("market.json").get("indices", [])
    reports = load("reports.json").get("items", [])
    intel = load("intel.json")

    # Date header (TPE)
    tpe = dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
    wd = "日一二三四五六"[tpe.weekday() if tpe.weekday() < 6 else (tpe.weekday() + 1) % 7]
    # weekday(): Mon=0..Sun=6 → 中文 mapping
    cn_wd = ["一", "二", "三", "四", "五", "六", "日"][tpe.weekday()]
    date_str = f"{tpe.month:02d}/{tpe.day:02d} (週{cn_wd})"

    lines = []
    lines.append(f"🌅 <b>{date_str} 鮪魚早安！</b>")
    lines.append("過去 24 小時重點整理 👇")
    lines.append("")

    # Today's thesis (from intel.json)
    if intel.get("thesis"):
        lines.append(f"🧠 <b>今日主軸</b>")
        lines.append(html_escape(intel["thesis"]))
        lines.append("")

    # Quick market snapshot
    snap_parts = []
    for m in market:
        if m["label"] in ("台股加權", "Nasdaq", "USD/TWD"):
            arrow = "▲" if (m.get("change_pct") or 0) >= 0 else "▼"
            snap_parts.append(html_escape(f"{m['label']} {m['price']:.2f} {arrow}{fmt_pct(m['change_pct'])}"))
    coins = crypto.get("coins", [])
    btc = next((c for c in coins if c["id"] == "bitcoin"), None)
    eth = next((c for c in coins if c["id"] == "ethereum"), None)
    if btc:
        arrow = "▲" if (btc.get("change_24h_pct") or 0) >= 0 else "▼"
        snap_parts.append(html_escape(f"BTC ${btc['price_usd']:,.0f} {arrow}{fmt_pct(btc['change_24h_pct'])}"))
    if eth:
        arrow = "▲" if (eth.get("change_24h_pct") or 0) >= 0 else "▼"
        snap_parts.append(html_escape(f"ETH ${eth['price_usd']:,.0f} {arrow}{fmt_pct(eth['change_24h_pct'])}"))
    fg = crypto.get("fear_greed")
    if fg:
        snap_parts.append(html_escape(f"F&G {fg['value']} ({fg['label']})"))

    if snap_parts:
        lines.append("📊 <b>市場快照</b>")
        # 兩個一行
        for i in range(0, len(snap_parts), 2):
            lines.append(" | ".join(snap_parts[i:i + 2]))
        lines.append("")

    # Categories
    cat_meta = [
        ("world", "🌍", "世界", 2),
        ("finance", "💰", "財經", 2),
        ("crypto", "🪙", "加密", 2),
        ("tech", "💻", "科技", 1),
        ("entertainment", "🎬", "影視", 1),
    ]
    for key, icon, tc, top_n in cat_meta:
        items = diversify(news.get(key, []), 2)[:top_n]
        if not items:
            continue
        lines.append(f"{icon} <b>{tc}</b>")
        for a in items:
            lines.append(f"• {html_escape(short(a['title']))}")
        lines.append("")

    # Reports — show 1 latest non-noise
    if reports:
        lines.append("📚 <b>機構新報告</b>")
        r = reports[0]
        lines.append(f"• <i>{html_escape(r['source'])}</i>: {html_escape(short(r['title'], 80))}")
        lines.append("")

    # Footer
    lines.append(f'🔗 <a href="{DASHBOARD_URL}">完整內容看 Dashboard</a>')

    return "\n".join(lines)


def send_telegram(text: str) -> dict:
    if not TOKEN or not CHAT_ID:
        raise RuntimeError("缺少 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID 環境變數")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


def main():
    print("Building daily brief...")
    msg = build_brief()
    print(f"Message length: {len(msg)} chars\n")
    print("=" * 50)
    print(msg)
    print("=" * 50)

    if "--dry-run" in sys.argv:
        print("\n[dry-run] 沒實際送出。")
        return

    print("\nSending to Telegram...")
    result = send_telegram(msg)
    print(f"Sent ✓ message_id = {result['result']['message_id']}")


if __name__ == "__main__":
    main()
