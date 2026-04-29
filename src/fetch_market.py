"""抓取股市與匯率資料 (yfinance)。"""
import sys
import json
import datetime as dt
from pathlib import Path
import yfinance as yf

from config import STOCK_TICKERS

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def safe_float(x):
    try:
        v = float(x)
        if v != v:
            return None
        return v
    except Exception:
        return None


def fetch_one(ticker: str, label: str):
    print(f"  → {label} ({ticker}) ...", end=" ", flush=True)
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d", interval="1d")
        if hist.empty or len(hist) < 1:
            print("no data")
            return None
        last = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) >= 2 else last
        price = safe_float(last["Close"])
        prev_close = safe_float(prev["Close"])
        change = price - prev_close if (price is not None and prev_close is not None) else None
        pct = (change / prev_close * 100) if (change is not None and prev_close) else None
        out = {
            "ticker": ticker,
            "label": label,
            "price": price,
            "prev_close": prev_close,
            "change": change,
            "change_pct": pct,
            "high": safe_float(last.get("High")),
            "low": safe_float(last.get("Low")),
            "volume": safe_float(last.get("Volume")),
            "as_of": last.name.isoformat() if hasattr(last.name, "isoformat") else str(last.name),
        }
        arrow = "+" if (pct or 0) >= 0 else ""
        print(f"{price:.2f} ({arrow}{pct:.2f}%)" if price is not None and pct is not None else "ok")
        return out
    except Exception as exc:
        print(f"FAIL ({exc.__class__.__name__})")
        return None


def main():
    DATA_DIR.mkdir(exist_ok=True)
    print("Fetching stock & FX...\n")
    rows = []
    for ticker, label in STOCK_TICKERS:
        r = fetch_one(ticker, label)
        if r:
            rows.append(r)

    payload = {
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "indices": rows,
    }
    target = DATA_DIR / "market.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDone → {target}")


if __name__ == "__main__":
    main()
