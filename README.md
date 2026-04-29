# 新聞看板 (News Dashboard) v0.1

每日全球資訊看板：世界 / 財經 / 加密 / 科技 / 影視 / 機構報告。

---

## 🚀 快速開始

### 1. 第一次使用（已完成）

Python 套件已安裝：`feedparser`, `yfinance`, `requests`

### 2. 抓取最新資料

```bash
cd C:\Users\wenny\Desktop\WorkSpace\新聞看板\src
python run_all.py
```

執行後：
- `data/news.json` — 約 290+ 篇新聞
- `data/crypto.json` — 5 大幣價 + 市值 + 恐慌指數
- `data/market.json` — 台股 / 美股 / 匯率
- `dashboard/index.html` — 完整 Dashboard

### 3. 每日早晨：編輯 Intelligence Layer（5-10 分鐘）

打開檔案：`data/intel.json`

每天早上看完早報後，編輯這個檔案的以下欄位：

| 欄位 | 內容 |
|------|------|
| `thesis` | 今日市場主軸（一句話） |
| `top_3_events` | 最重要 3 件事（每筆含 event + implication） |
| `why_it_matters` | 為什麼重要（3 點） |
| `what_changed` | 數據變化（3-4 點） |
| `cross_signals` | 跨資產連動訊號 |
| `section_signals` | 各分類一句重點（world/finance/crypto/tech/entertainment） |
| `report_takeaways` | 機構報告 key takeaway（key 用標題部分字串即可，會自動匹配） |

> 重要：`run_all.py` 與「立即更新」按鈕**不會覆蓋** `intel.json`，只更新新聞與市場資料，所以你的分析會保留。

存檔後，按右下角「⟳ 立即更新」或重新打開 Dashboard 即可看到新的 Intelligence Layer。

### 4. 打開 Dashboard

**兩種模式：**

#### 🟢 完整模式（推薦，可用「立即更新」按鈕）
```bash
cd C:\Users\wenny\Desktop\WorkSpace\新聞看板
python src\serve.py
```
- 會自動開啟瀏覽器到 `http://localhost:8765`
- 右下角的「⟳ 立即更新」按鈕**可以用**（30 秒抓最新）
- 按 `Ctrl+C` 停止伺服器

#### 🟡 快速檢視模式（雙擊即可）
雙擊：`dashboard/index.html`
- 看的是上次抓取的資料
- 右下角按鈕會顯示「需要本機伺服器」提示

---

## 📁 目錄結構

```
新聞看板/
├── README.md                       ← 本文件
├── docs/
│   └── 2026-04-29-新聞看板-設計文件.md
├── src/
│   ├── config.py                   ← 來源清單（要加減新聞網站改這裡）
│   ├── fetch_news.py               ← RSS 抓取
│   ├── fetch_crypto.py             ← 加密市場
│   ├── fetch_market.py             ← 股市/匯率
│   ├── build_dashboard.py          ← 把資料嵌入 HTML
│   └── run_all.py                  ← 一鍵跑全部
├── data/                           ← 抓取後的 JSON（自動生成）
│   ├── news.json
│   ├── crypto.json
│   └── market.json
└── dashboard/
    ├── template.html               ← Dashboard 模板（含 placeholder）
    └── index.html                  ← 帶資料的最終 Dashboard ⭐
```

---

## 🔧 常見操作

### 想加新聞來源
編輯 `src/config.py` 裡的 `RSS_SOURCES`，重跑 `python run_all.py`。

### 想換加密幣
編輯 `src/config.py` 裡的 `CRYPTO_COINS`，可選清單見 [CoinGecko](https://www.coingecko.com/en/coins)。

### 想加股票/指數
編輯 `src/config.py` 裡的 `STOCK_TICKERS`，代號見 [Yahoo Finance](https://finance.yahoo.com/)。

---

## 📅 v0.1 範圍

- ✅ 22 個資料來源 RSS 抓取
- ✅ 加密貨幣即時行情
- ✅ 全球指數 / 匯率
- ✅ The Economist 風格 Dashboard
- ✅ WhatsApp 訊息預覽
- ❌ AI 摘要（待 Claude API key）
- ❌ WhatsApp 推播（待 CallMeBot 設定）
- ❌ GitHub Pages 部署（待下一階段）
- ❌ 機構報告掃描（Phase 2）

---

## 🐛 已知限制

- Reuters 沒有官方 RSS，改用 Google News RSS 抓取
- CNN Business RSS 條目較少（可能 feed 被精簡），影響不大
- 股市資料是收盤價，非即時（盤中可能延遲 15-30 分）

---

## 📝 下一階段

詳見 `docs/2026-04-29-新聞看板-設計文件.md` 第 10 節。
