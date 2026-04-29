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


def visual_width(s: str) -> int:
    """近似 monospace 顯示寬度：CJK 字佔 2 格、其餘 1 格。"""
    w = 0
    for c in s:
        cp = ord(c)
        if (0x1100 <= cp <= 0x115F or 0x2E80 <= cp <= 0x9FFF or
            0xA000 <= cp <= 0xA4CF or 0xAC00 <= cp <= 0xD7A3 or
            0xF900 <= cp <= 0xFAFF or 0xFE30 <= cp <= 0xFE4F or
            0xFF00 <= cp <= 0xFF60 or 0xFFE0 <= cp <= 0xFFE6):
            w += 2
        else:
            w += 1
    return w


def pad_right(s: str, width: int) -> str:
    """補足右側到指定的 visual 寬度。"""
    return s + " " * max(0, width - visual_width(s))


def pad_left(s: str, width: int) -> str:
    """補足左側到指定的 visual 寬度（右對齊）。"""
    return " " * max(0, width - visual_width(s)) + s


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

    # 依當下 TPE 時間切換早安 / 晚安
    is_evening = tpe.hour >= 14
    if is_evening:
        icon = "🌙"
        greet = "鮪魚晚安！"
        intro = "日終市場 + 今日重點整理"
    else:
        icon = "☀️"
        greet = "鮪魚早安！"
        intro = "過去 24 小時重點整理"

    lines = []
    lines.append(f"{icon} <b>{date_str} {greet}</b>")
    lines.append(intro)
    lines.append("")

    # Today's thesis (from intel.json)
    if intel.get("thesis"):
        lines.append("<b>今日主軸</b>")
        lines.append(html_escape(intel["thesis"]))
        lines.append("")

    # Quick market snapshot — 用 <pre> 等寬字體對齊
    rows = []  # (label, price_str, pct_str)
    for m in market:
        if m["label"] in ("台股加權", "Nasdaq", "USD/TWD"):
            rows.append((
                m["label"],
                f"{m['price']:,.2f}",
                fmt_pct(m["change_pct"]),
            ))
    coins = crypto.get("coins", [])
    btc = next((c for c in coins if c["id"] == "bitcoin"), None)
    eth = next((c for c in coins if c["id"] == "ethereum"), None)
    if btc:
        rows.append(("BTC", f"${btc['price_usd']:,.0f}", fmt_pct(btc["change_24h_pct"])))
    if eth:
        rows.append(("ETH", f"${eth['price_usd']:,.0f}", fmt_pct(eth["change_24h_pct"])))
    fg = crypto.get("fear_greed")
    if fg:
        rows.append(("F&G", f"{fg['value']} ({fg['label']})", ""))

    if rows:
        # 計算各欄需要的寬度（visual width，含 CJK）
        label_w = max(visual_width(r[0]) for r in rows)
        price_w = max(visual_width(r[1]) for r in rows)
        # pct 寬度固定 7（如 "-99.99%"）
        aligned = []
        for label, price, pct in rows:
            line = f"{pad_right(label, label_w)}  {pad_left(price, price_w)}  {pct}"
            aligned.append(line.rstrip())
        lines.append("<b>市場快照</b>")
        lines.append("<pre>" + html_escape("\n".join(aligned)) + "</pre>")
        lines.append("")

    # Categories — 留 icon 增加掃視速度
    cat_meta = [
        ("world", "🌍", "世界", 2),
        ("finance", "💰", "財經", 2),
        ("crypto", "🪙", "加密", 2),
        ("tech", "💻", "科技", 2),
        ("entertainment", "🎬", "影視", 2),
    ]
    for key, icon, tc, top_n in cat_meta:
        items = diversify(news.get(key, []), 2)[:top_n]
        if not items:
            continue
        lines.append(f"{icon} <b>{tc}</b>")
        for a in items:
            lines.append(f"• {html_escape(short(a['title']))}")
        lines.append("")

    # Reports — show top 2 latest
    if reports:
        lines.append("📚 <b>機構新報告</b>")
        for r in reports[:2]:
            lines.append(f"• <i>{html_escape(r['source'])}</i>: {html_escape(short(r['title'], 80))}")
        lines.append("")

    # Footer
    lines.append(f'<a href="{DASHBOARD_URL}">完整內容看 Dashboard</a>')

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
