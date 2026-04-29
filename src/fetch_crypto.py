"""抓取加密貨幣市場資料 (CoinGecko + Alternative.me)。"""
import sys
import json
import datetime as dt
from pathlib import Path
import requests

from config import CRYPTO_COINS, REQUEST_TIMEOUT, USER_AGENT

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
COINGECKO = "https://api.coingecko.com/api/v3"
FEAR_GREED = "https://api.alternative.me/fng/"


def fetch_coins():
    print("  → CoinGecko coins ...", end=" ", flush=True)
    ids = ",".join(CRYPTO_COINS)
    url = f"{COINGECKO}/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ids,
        "order": "market_cap_desc",
        "price_change_percentage": "24h,7d",
    }
    r = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    out = []
    for c in data:
        out.append({
            "id": c["id"],
            "symbol": c["symbol"].upper(),
            "name": c["name"],
            "image": c.get("image"),
            "price_usd": c.get("current_price"),
            "market_cap_usd": c.get("market_cap"),
            "total_volume_usd": c.get("total_volume"),
            "change_24h_pct": c.get("price_change_percentage_24h_in_currency"),
            "change_7d_pct": c.get("price_change_percentage_7d_in_currency"),
            "high_24h": c.get("high_24h"),
            "low_24h": c.get("low_24h"),
        })
    print(f"{len(out)} coins")
    return out


def fetch_global():
    print("  → CoinGecko global ...", end=" ", flush=True)
    url = f"{COINGECKO}/global"
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    d = r.json()["data"]
    out = {
        "total_market_cap_usd": d["total_market_cap"]["usd"],
        "total_volume_usd": d["total_volume"]["usd"],
        "btc_dominance": d["market_cap_percentage"].get("btc"),
        "eth_dominance": d["market_cap_percentage"].get("eth"),
        "market_cap_change_24h_pct": d.get("market_cap_change_percentage_24h_usd"),
        "active_cryptocurrencies": d.get("active_cryptocurrencies"),
    }
    print(f"market cap ${out['total_market_cap_usd']/1e12:.2f}T")
    return out


def fetch_fear_greed():
    print("  → Fear & Greed Index ...", end=" ", flush=True)
    r = requests.get(FEAR_GREED, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    d = r.json()["data"][0]
    out = {
        "value": int(d["value"]),
        "label": d["value_classification"],
        "timestamp": dt.datetime.fromtimestamp(int(d["timestamp"]), tz=dt.timezone.utc).isoformat(),
    }
    print(f"{out['value']} ({out['label']})")
    return out


def main():
    DATA_DIR.mkdir(exist_ok=True)
    print("Fetching crypto market...\n")
    payload = {
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "coins": fetch_coins(),
        "global": fetch_global(),
        "fear_greed": fetch_fear_greed(),
    }
    target = DATA_DIR / "crypto.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDone → {target}")


if __name__ == "__main__":
    main()
