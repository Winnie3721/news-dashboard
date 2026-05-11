# 新聞看板 — AI 自動生成 Intelligence Layer 設計

- **建立日期**：2026-05-11
- **作者**：wenny + Claude
- **狀態**：草稿（待使用者確認）
- **替換對象**：目前 `data/intel.json` 的手動編輯流程

---

## 1. 背景與目標

### 1.1 現況
- Dashboard 上「🧠 今日洞察」區塊（thesis、Top 3、Why It Matters、Cross Signals）完全由 `data/intel.json` 驅動。
- `intel.json` 目前 `edited_at = 2026-04-29`，距今 12 天未更新。
- 失敗原因：手動編輯流程摩擦大（JSON 易壞、需要 GitHub 網頁/IDE、要寫 7 個欄位）。
- 目前 README 標註 `❌ AI 摘要（待 Claude API key）`——本案完成此項。

### 1.2 目標
- **零人工**：使用者完全不需要每日編輯 `intel.json`。
- **品質不降**：自動生成內容必須維持目前 `intel.json` 的具體性、因果鏈、數據引用密度。不容空話。
- **零金錢成本**：使用 Google Gemini API 免費額度，不需付費。
- **保留逃生門**：使用者偶爾想手動覆寫時仍可。

### 1.3 非目標（明確排除）
- 半自動審核（Telegram 確認再 commit）—— 已評估後選擇放棄。
- Claude API / OpenAI API 付費方案。
- 本機 Ollama（需要 PC 永遠開機，與現有 GitHub Actions 排程衝突）。
- 為新欄位修改 Dashboard 視覺——本案不動 `dashboard/template.html`。

---

## 2. 系統架構

### 2.1 整體流程（修改後）

```
GitHub Actions (06:00 / 17:00 TPE，update.yml)
  │
  ├─ Step 1: fetch_news.py
  ├─ Step 2: fetch_crypto.py
  ├─ Step 3: fetch_market.py
  ├─ Step 4: fetch_reports.py
  ├─ Step 5: 【新】generate_intel.py    ← 本案新增
  │           │
  │           ├─ 載入 news/crypto/market/reports JSON
  │           ├─ 檢查 data/intel.override.json 是否存在
  │           │   └─ 若存在：直接複製為 intel.json，跳過 AI 呼叫
  │           ├─ 否則：呼叫 Gemini API
  │           ├─ JSON schema 驗證
  │           ├─ 數字交叉驗證（regex vs market.json）
  │           ├─ 失敗則重試 1 次
  │           ├─ 若最終失敗：保留昨日 intel.json + 寫入失敗計數
  │           └─ 若連續 3 天失敗：呼叫 send_telegram_alert.py
  │
  ├─ Step 6: build_dashboard.py
  ├─ Step 7: commit & push
  ├─ Step 8: wait until 07:15 / 18:15 TPE
  └─ Step 9: send_telegram.py（每日 brief）
```

### 2.2 新增 / 修改檔案

| 檔案 | 狀態 | 用途 |
|------|------|------|
| `src/generate_intel.py` | 新增 | 主邏輯：呼叫 Gemini、驗證、寫檔、處理失敗 |
| `src/intel_prompt.py` | 新增 | System prompt + few-shot 範例（與主邏輯分離，方便調整） |
| `src/intel_validator.py` | 新增 | JSON schema 驗證 + 數字交叉驗證 |
| `src/run_all.py` | 修改 | 在 `build_dashboard.py` 之前插入 `generate_intel.py` |
| `.github/workflows/update.yml` | 修改 | 新增 `GEMINI_API_KEY` 環境變數 |
| `requirements.txt` | 修改 | 新增 `google-genai`、`jsonschema` |
| `data/intel.override.json` | 不建立（不存在即代表停用） | 使用者手動覆寫專用 |
| `data/.intel_failures` | 新增 | 純文字單一整數，記錄連續失敗次數 |
| `data/intel.json` | 仍存在 | 由 generate_intel.py 寫入 |

---

## 3. Prompt 設計

### 3.1 設計原則：防空洞四層

1. **引用強制**：每欄位要求引用輸入資料中的具體新聞或數字。
2. **Few-shot 對照**：示範好 vs 壞範例，讓模型內化「空話」的長相。
3. **自我檢查清單**：要求模型在內部 review 後才輸出（chain-of-thought 不外洩）。
4. **風格 DNA 鎖定**：用 `→` 連接因果、繁中、無修飾形容詞、每點 30–50 字。

### 3.2 System Prompt（完整草稿）

```
你是新聞看板的資深市場觀察員。任務：根據今日抓取的新聞、市場、加密、機構報告數據，產出當日 intel.json。

# 鐵則（違反任何一條都視為失敗）

1. 引用強制：每一個結論必須能對應到輸入資料中的「具體新聞標題」或「具體數字」。
2. 禁用空泛詞：「結構性」、「持續」、「長期」、「全面」、「廣泛」、「趨勢」——除非你能引用至少 3 個獨立數據點支撐。
3. 禁止填空：輸入資料沒提到的事件、人物、數字，絕對不可寫入。
4. 數字精確：股市 / 匯率必須帶單位與漲跌幅（例如 "Nasdaq -0.90%"）；新聞引用必須帶來源名（例如 "(CNBC)"）。
5. 風格：簡潔、因果用「→」連接、不寫修飾性形容詞、繁體中文。
6. 寧缺勿濫：若某欄位沒有足夠數據支撐，回傳空陣列 `[]` 或 `null`，不要硬填。

# 範例（學起來，輸出時模仿）

## 好 thesis
"全球同步修正、避險旋轉浮現；澳洲通膨意外走低，重新點燃降息預期"
為什麼好：兩個事件都對應輸入資料——指數同步下跌的具體數字 + 澳洲 CPI 新聞。

## 壞 thesis（不可這樣寫）
"市場面臨結構性挑戰，投資情緒謹慎，未來走向尚待觀察"
為什麼壞：「結構性」「謹慎」「尚待觀察」三個套話、無一條對應輸入資料。

## 好 cross_signal
"通膨 ↓ → 利率預期 ↓ → Nasdaq 中期估值利多 vs 短線壓力"
為什麼好：明確因果鏈、可驗證、提到具體資產。

## 壞 cross_signal（不可這樣寫）
"市場各環節相互影響，需要綜合考量。"
為什麼壞：空話。

## 好 what_changed
"全球指數同步下跌：台股 -0.86%、Nasdaq -0.90%、日經 -1.02%、S&P -0.49%"
為什麼好：四個具體數字，全部能在 market.json 找到。

## 壞 what_changed（不可這樣寫）
"市場呈現下跌格局，投資人情緒受影響"
為什麼壞：無具體數字、寫了「投資人情緒」這種無法驗證的話。

# 輸出格式（純 JSON，不加任何前後說明文字）

{
  "edited_at": "<填入提供的時間戳>",
  "edited_by": "ai-auto-v1",
  "thesis": "string，30-50 字，必須引用至少一個輸入資料中的具體事件或數字",
  "top_3_events": [
    {
      "event": "string，從輸入挑出的具體事件，含關鍵主詞",
      "source": "輸入資料中的來源名",
      "implication": "一句話因果，必須引用 market.json 或 crypto.json 的具體數字"
    }
  ],
  "why_it_matters": [
    "string，3 點，每點必須引用至少一個數據"
  ],
  "what_changed": [
    "string，3-4 點，必須包含具體數字與漲跌幅"
  ],
  "cross_signals": [
    "string，3-4 條因果鏈，用 → 連接，必須提到具體資產或數據"
  ],
  "section_signals": {
    "world": "→ 一句話，必須引用 world 分類中的具體新聞",
    "finance": "→ ...",
    "crypto": "→ ...",
    "tech": "→ ...",
    "entertainment": "→ ..."
  },
  "report_takeaways": {
    "報告標題前綴": "一句重點，必須對應該報告"
  }
}

# 輸入資料

時間戳：{timestamp}

## 市場數據（market.json）
{market_data}

## 加密數據（crypto.json）
{crypto_data}

## 新聞標題（各分類 Top 8）
{news_titles}

## 機構報告（reports.json，最多 10 篇）
{reports}

# 內部自我檢查（執行後才能輸出）

逐條檢視你寫好的 JSON：
- thesis 中的每個事件能在 market_data 或 news_titles 找到嗎？
- top_3_events 的 implication 都帶具體數字嗎？
- what_changed 每行都有 % 或數字嗎？
- cross_signals 每條都提到具體資產或指數嗎？
- 是否有任何欄位用了「結構性」「持續」「長期」「全面」「廣泛」？若有→重寫。
- report_takeaways 的 key 是否真的對應 reports 輸入中的標題前綴？

通過全部檢查後輸出 JSON，否則重寫直到通過。
```

### 3.3 Input 組裝策略

- `market_data`：原樣傳入（小，~2KB）。
- `crypto_data`：原樣傳入（小，~3KB）。
- `news_titles`：**只傳標題 + 來源 + 分類**，不傳全文摘要。每類取 Top 8（按 published 排序），總共 5 類 × 8 = 40 條，約 5KB。
- `reports`：只傳標題 + 來源，最多 10 篇，約 1KB。

合計輸入約 12KB（≈ 4K tokens）。輸出約 1K tokens。雙跑/天約 10K tokens/天，遠低於 Gemini 2.5 Flash 免費 1M tokens/天上限。

---

## 4. 驗證層（intel_validator.py）

### 4.1 JSON Schema 驗證
- 使用 `jsonschema` 套件。
- Schema 定義必填欄位、型別、`top_3_events` 至少 3 項、`section_signals` 五個 key 齊全。
- 失敗 → 觸發重試。

### 4.2 數字交叉驗證
- 從 `intel.json` 中 regex 抽出所有形如 `-?\d+\.\d{2}%` 或 `\$\d{1,3}(,\d{3})*` 的數字。
- 對照 `market.json`、`crypto.json` 中的原始數字。
- 容忍誤差：百分比類數字（如 `-0.86%`）容忍絕對誤差 ±0.05 個百分點；價格類數字（如 `$76,000`）容忍相對誤差 ±0.5%（避免四捨五入或盤中變動鬧翻）。
- 若有 ≥1 個數字找不到對應 → 標記「可能幻覺」並觸發重試。
- 二次仍失敗 → 進入「保留昨日」失敗處理流程。

### 4.3 空泛詞掃描
- Regex 偵測：「結構性」「持續」「長期增長」「全面」「廣泛」
- 命中 → 重試。

---

## 5. Override 機制

### 5.1 規則
- 若 `data/intel.override.json` 存在 → `generate_intel.py` 直接 `shutil.copy()` 為 `intel.json`、**完全跳過 Gemini 呼叫**。
- 若不存在 → 走正常 AI 流程。

### 5.2 使用情境
- 使用者偶爾覺得 AI 寫得爛、想自己改一天 → 手動建立 `intel.override.json`。
- 用完想恢復自動 → 刪掉檔案即可。
- 永久切回手動 → 留著 `intel.override.json` 一直不刪。

### 5.3 提示
- `generate_intel.py` 在 log 中明確輸出 `[OVERRIDE] 使用 intel.override.json，跳過 AI 生成`，讓使用者在 GitHub Actions 介面一眼看到。

---

## 6. 失敗處理

### 6.1 單次失敗（API 錯誤 / 驗證失敗）
- 重試 1 次（間隔 5 秒）。
- 二次仍失敗 → 進入「保留」流程。

### 6.2 保留流程
- **不覆寫 `intel.json`**。Dashboard 仍顯示昨日內容。
- 將 `data/.intel_failures` 的整數加 1。
- log 印出 `[FAIL] 保留昨日 intel.json，連續失敗 N 次`。

### 6.3 連續失敗警報
- 若 `.intel_failures >= 3`，呼叫 Telegram 推一則簡短訊息：
  > ⚠️ 新聞看板 AI Intel 已連續失敗 3 次。請檢查 GitHub Actions log。
- 警報發送後重設 `.intel_failures = 0`（避免天天炸警報）。

### 6.4 成功流程
- 每次成功生成 → 將 `.intel_failures` 重設為 0。

---

## 7. 環境變數與設定

### 7.1 新增 GitHub Secrets
- `GEMINI_API_KEY`：使用者自行至 [aistudio.google.com](https://aistudio.google.com/) 申請（免費）。

### 7.2 update.yml 修改片段
```yaml
- name: Run pipeline
  working-directory: src
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
    TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
  run: python run_all.py
```

### 7.3 模型選擇
- 預設：`gemini-2.5-flash`（免費、品質夠、快）。
- 若日後想升級：改 `intel_prompt.py` 中的 `MODEL_NAME` 常數即可（呼叫端不動）。

---

## 8. 邊界與已知限制

| 項目 | 說明 |
|------|------|
| Gemini 免費額度若被砍 | 設計上是「可換 LLM」——換成 OpenRouter 免費模型或 GitHub Models 只需改 client 初始化 |
| Gemini API 偶爾掛掉 | 失敗保留昨日 intel.json，不影響其他資料更新 |
| 模型仍可能產生幻覺數字 | 數字交叉驗證會抓得到，會觸發重試 |
| Few-shot 風格 drift | 預期 1–2 週內檢視一次輸出品質，必要時加新範例 |
| `intel.override.json` 一直存在 | 等於停用自動化。使用者需自我管理 |

---

## 9. 測試策略

### 9.1 單元測試（手動 dry-run）
1. 在本機 export `GEMINI_API_KEY=...`，執行 `python src/generate_intel.py --dry-run`。
2. 預期：產出印到 stdout，不寫檔。
3. 人工檢查：thesis、top_3、cross_signals 是否符合品質標準。

### 9.2 驗證層測試
1. 故意餵一個包含「結構性」的假 JSON → 應觸發重試。
2. 故意餵一個含 `Nasdaq -99.99%` 假數字的 JSON → 數字交叉驗證應抓到。

### 9.3 整合測試
1. 在 GitHub 介面手動觸發 `workflow_dispatch`。
2. 檢查 Actions log 是否有 `[OK] intel.json 已更新` 訊息。
3. 檢查 Dashboard 線上版「🧠 今日洞察」是否反映新內容。

### 9.4 Override 測試
1. 建立 `data/intel.override.json` 後手動觸發。
2. 預期：log 印 `[OVERRIDE]`，Dashboard 內容 = override 檔案內容。

---

## 10. 上線後監控

- **第一週**：每日早上看 Dashboard 一次，主觀評分 1–5 分。
- **品質警訊**：若連續 3 天評分 ≤ 2，回到 prompt 加新 few-shot 範例。
- **失敗警訊**：依賴 §6.3 自動 Telegram 警報。

---

## 11. 未來擴充（不在本案範圍）

- 每日輸出後備份 `intel.json` 到 `data/archive/intel-YYYY-MM-DD.json` 做歷史追蹤。
- 接 Claude API 作為 fallback（Gemini 失敗時自動切換）。
- 加入「對比昨日」欄位（thesis_yesterday、what_changed_vs_yesterday）。
- Dashboard 上加「AI 生成」徽章與最後生成時間（讓使用者一眼看到是 AI 還是 override）。
