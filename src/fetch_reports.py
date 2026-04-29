"""抓取機構報告 (McKinsey / Goldman / IMF / WEF / CFR / World Bank / BCG / Bain / PwC / Deloitte / TAICCA)。

策略：用 Google News RSS 搜尋各機構網域，沒有時間限制 → 自動拿到最近 30 天能搜到的報告/研究。
這樣即使本週沒有新報告，仍能顯示前幾週/月的報告，避免 Dashboard 留白。
"""
import sys
import json
import time
import datetime as dt
from pathlib import Path
import feedparser

from config import REPORT_SOURCES, USER_AGENT

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def parse_published(entry) -> str:
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            try:
                return dt.datetime(*t[:6], tzinfo=dt.timezone.utc).isoformat()
            except Exception:
                continue
    return dt.datetime.now(dt.timezone.utc).isoformat()


def clean_title(t: str) -> str:
    """Google News 標題常會帶尾巴 ' - <出版社名>'，移除以保乾淨。"""
    if not t:
        return ""
    parts = t.rsplit(" - ", 1)
    if len(parts) == 2 and len(parts[1]) < 40:
        return parts[0].strip()
    return t.strip()


# 排除非報告/研究的雜訊（職缺、團隊介紹、聯絡頁等）
NOISE_PATTERNS = [
    # 職缺
    "Senior Analyst", "Senior Manager", "Senior Consultant", "Senior Associate",
    "Junior Analyst", "Job Description", "We are hiring", "Apply Now",
    "Career", "Vacancy", "Position", "招募", "徵才", "職缺",
    # 公司介紹/導覽
    "經營團隊", "關於我們", "聯絡我們", "公司簡介", "組織架構", "About Us",
    "Contact Us", "Privacy Policy", "Terms of Use", "Cookie",
    "登入", "註冊", "Login", "Register", "Sign Up",
    "新聞中心", "首頁",
    # 行政
    "Site Map", "網站地圖",
]


def is_noise(title: str) -> bool:
    if not title or len(title.strip()) < 10:
        return True
    t = title.lower()
    for p in NOISE_PATTERNS:
        if p.lower() in t:
            return True
    return False


def fetch_one(name: str, url: str):
    print(f"  → {name} ...", end=" ", flush=True)
    try:
        feed = feedparser.parse(
            url,
            agent=USER_AGENT,
            request_headers={"Accept": "application/rss+xml, application/xml, text/xml"},
        )
        items = []
        skipped = 0
        for e in feed.entries[:15]:
            title = clean_title(e.get("title", ""))
            if is_noise(title):
                skipped += 1
                continue
            items.append({
                "title": title,
                "link": e.get("link", ""),
                "published": parse_published(e),
                "source": name,
            })
            if len(items) >= 10:
                break
        msg = f"{len(items)} reports"
        if skipped:
            msg += f" (skipped {skipped} noise)"
        print(msg)
        return items
    except Exception as exc:
        print(f"FAIL ({exc.__class__.__name__})")
        return []


def main():
    DATA_DIR.mkdir(exist_ok=True)
    print("Fetching institutional reports...\n")
    all_items = []
    for name, url in REPORT_SOURCES:
        all_items.extend(fetch_one(name, url))
        time.sleep(0.4)

    # 排序：最新的在前
    all_items.sort(key=lambda x: x["published"], reverse=True)

    payload = {
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "items": all_items,
        "totals_by_source": {},
    }
    for it in all_items:
        s = it["source"]
        payload["totals_by_source"][s] = payload["totals_by_source"].get(s, 0) + 1

    target = DATA_DIR / "reports.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDone. {len(all_items)} reports → {target}")


if __name__ == "__main__":
    main()
