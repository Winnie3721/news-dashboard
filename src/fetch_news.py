"""抓取所有 RSS 來源並輸出到 data/news.json。"""
import sys
import json
import time
import datetime as dt
from pathlib import Path
import feedparser

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from config import RSS_SOURCES, CATEGORY_META, USER_AGENT, REQUEST_TIMEOUT, BLACKLIST_KEYWORDS

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


def clean_summary(text: str, limit: int = 220) -> str:
    if not text:
        return ""
    import re
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[:limit].rstrip() + "…"
    return text


def fetch_feed(name: str, url: str, weight: int, category: str):
    print(f"  → {name} ...", end=" ", flush=True)
    try:
        feed = feedparser.parse(
            url,
            agent=USER_AGENT,
            request_headers={"Accept": "application/rss+xml, application/xml, text/xml"},
        )
        items = []
        for e in feed.entries[:15]:
            items.append({
                "title": (e.get("title") or "").strip(),
                "link":  e.get("link") or "",
                "summary": clean_summary(e.get("summary", "")),
                "published": parse_published(e),
                "source": name,
                "source_weight": weight,
                "category": category,
            })
        print(f"{len(items)} items")
        return items
    except Exception as exc:
        print(f"FAIL ({exc.__class__.__name__})")
        return []


def is_blacklisted(title: str, category: str) -> bool:
    bl = BLACKLIST_KEYWORDS.get(category, [])
    if not bl:
        return False
    t = (title or "").lower()
    for kw in bl:
        if kw.lower() in t:
            return True
    return False


def fetch_all() -> dict:
    out = {}
    for category, sources in RSS_SOURCES.items():
        print(f"[{CATEGORY_META[category]['icon']} {category}]")
        items = []
        for name, url, weight in sources:
            items.extend(fetch_feed(name, url, weight, category))
            time.sleep(0.3)
        before = len(items)
        items = [x for x in items if not is_blacklisted(x["title"], category)]
        filtered = before - len(items)
        if filtered:
            print(f"  (過濾掉 {filtered} 篇生活/非業務類)")
        items.sort(key=lambda x: x["published"], reverse=True)
        out[category] = items
    return out


def main():
    DATA_DIR.mkdir(exist_ok=True)
    print("Fetching RSS feeds...\n")
    data = fetch_all()

    payload = {
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "categories": data,
        "totals": {k: len(v) for k, v in data.items()},
    }
    target = DATA_DIR / "news.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(payload["totals"].values())
    print(f"\nDone. {total} articles → {target}")


if __name__ == "__main__":
    main()
