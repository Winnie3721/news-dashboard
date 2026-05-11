# Auto Intel Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用 Google Gemini API（免費額度）自動生成新聞看板的 `data/intel.json`，取代每日手動編輯，並具備驗證、Override、失敗保護三層機制。

**Architecture:** 在現有 GitHub Actions pipeline（`update.yml`）中、`build_dashboard.py` 之前插入新的 `generate_intel.py`。新增 3 個小型純邏輯模組（prompt、validator、failure_tracker）並用 TDD 開發，主腳本以 mock 測試協調流程。Override 機制以 `intel.override.json` 是否存在為開關。

**Tech Stack:** Python 3.12、`google-genai`（Gemini SDK）、`jsonschema`、`pytest`、現有 GitHub Actions workflow。

---

## File Structure

### 新增檔案

| 路徑 | 責任 |
|------|------|
| `src/intel_prompt.py` | System prompt 常數、few-shot 範例、輸入組裝函式 |
| `src/intel_validator.py` | JSON schema 驗證 + 數字交叉驗證 + 空泛詞掃描 |
| `src/intel_failure_tracker.py` | 讀寫 `.intel_failures` 計數、判斷是否觸發 Telegram 警報 |
| `src/generate_intel.py` | 主協調流程：載入資料 → 檢查 override → 呼叫 Gemini → 驗證 → 寫檔 / 失敗處理 |
| `tests/__init__.py` | 空檔，標記為 package |
| `tests/test_intel_validator.py` | 驗證層單元測試 |
| `tests/test_intel_failure_tracker.py` | 失敗計數單元測試 |
| `tests/test_intel_prompt.py` | 輸入組裝測試 |
| `tests/test_generate_intel.py` | 主流程測試（mock Gemini） |
| `pytest.ini` | pytest 設定（指定 src/ 為 source path） |

### 修改檔案

| 路徑 | 修改 |
|------|------|
| `requirements.txt` | 新增 `google-genai`, `jsonschema`, `pytest` |
| `src/run_all.py` | SCRIPTS 加入 `generate_intel.py`，順序：fetch_* → generate_intel → build_dashboard |
| `.github/workflows/update.yml` | Pipeline 步驟新增 `GEMINI_API_KEY` 環境變數 |

### 自動產生（不需手動建立）

- `data/.intel_failures` — 由 `intel_failure_tracker` 寫入
- `data/intel.json` — 由 `generate_intel.py` 寫入
- `data/intel.override.json` — 使用者自行建立（不存在即代表自動模式）

---

## Task 1: 安裝依賴與 pytest 基礎設施

**Files:**
- Modify: `requirements.txt`
- Create: `pytest.ini`
- Create: `tests/__init__.py`

- [ ] **Step 1: 更新 requirements.txt**

修改 `C:\Users\wenny\Desktop\WorkSpace\新聞看板\requirements.txt`：

```
feedparser>=6.0
yfinance>=0.2
requests>=2.31
google-genai>=0.3.0
jsonschema>=4.20
pytest>=8.0
```

- [ ] **Step 2: 安裝依賴**

```bash
cd C:\Users\wenny\Desktop\WorkSpace\新聞看板
pip install -r requirements.txt
```

Expected: `Successfully installed google-genai-... jsonschema-... pytest-...`

- [ ] **Step 3: 建立 pytest.ini**

Create `C:\Users\wenny\Desktop\WorkSpace\新聞看板\pytest.ini`：

```ini
[pytest]
pythonpath = src
testpaths = tests
python_files = test_*.py
```

- [ ] **Step 4: 建立 tests/__init__.py**

Create `C:\Users\wenny\Desktop\WorkSpace\新聞看板\tests\__init__.py`（空檔案，但建立它讓 pytest 識別為 package）。

- [ ] **Step 5: 驗證 pytest 跑得起來**

```bash
cd C:\Users\wenny\Desktop\WorkSpace\新聞看板
pytest --collect-only
```

Expected: `no tests ran`（還沒寫測試，正常）

- [ ] **Step 6: Commit**

```bash
cd C:\Users\wenny\Desktop\WorkSpace\新聞看板
git add requirements.txt pytest.ini tests/__init__.py
git commit -m "chore: add Gemini SDK, jsonschema, pytest for auto-intel feature"
```

---

## Task 2: intel_failure_tracker.py (TDD)

**責任：** 讀寫 `data/.intel_failures` 純文字檔（內容為一個整數），提供「+1、重設、判斷是否警報」三個操作。

**Files:**
- Test: `tests/test_intel_failure_tracker.py`
- Create: `src/intel_failure_tracker.py`

- [ ] **Step 1: 寫失敗的測試**

Create `C:\Users\wenny\Desktop\WorkSpace\新聞看板\tests\test_intel_failure_tracker.py`：

```python
"""Unit tests for intel_failure_tracker."""
import pytest
from pathlib import Path
from intel_failure_tracker import FailureTracker


@pytest.fixture
def tracker(tmp_path):
    return FailureTracker(tmp_path / ".intel_failures")


def test_default_count_when_file_missing(tracker):
    assert tracker.count() == 0


def test_record_failure_increments(tracker):
    tracker.record_failure()
    assert tracker.count() == 1
    tracker.record_failure()
    assert tracker.count() == 2


def test_reset_to_zero(tracker):
    tracker.record_failure()
    tracker.record_failure()
    tracker.reset()
    assert tracker.count() == 0


def test_should_alert_returns_false_below_threshold(tracker):
    tracker.record_failure()
    tracker.record_failure()
    assert tracker.should_alert(threshold=3) is False


def test_should_alert_returns_true_at_threshold(tracker):
    tracker.record_failure()
    tracker.record_failure()
    tracker.record_failure()
    assert tracker.should_alert(threshold=3) is True


def test_alert_resets_counter(tracker):
    """When alert fires, counter resets so we don't spam every run."""
    for _ in range(3):
        tracker.record_failure()
    assert tracker.should_alert(threshold=3) is True
    tracker.reset()
    assert tracker.count() == 0


def test_corrupt_file_treated_as_zero(tracker, tmp_path):
    """If someone manually writes junk into the counter file, don't crash."""
    (tmp_path / ".intel_failures").write_text("not a number", encoding="utf-8")
    assert tracker.count() == 0
```

- [ ] **Step 2: 跑測試確認 fail**

```bash
cd C:\Users\wenny\Desktop\WorkSpace\新聞看板
pytest tests/test_intel_failure_tracker.py -v
```

Expected: `ModuleNotFoundError: No module named 'intel_failure_tracker'`

- [ ] **Step 3: 實作 intel_failure_tracker.py**

Create `C:\Users\wenny\Desktop\WorkSpace\新聞看板\src\intel_failure_tracker.py`：

```python
"""記錄 intel 生成連續失敗次數，判斷是否要觸發警報。"""
from pathlib import Path


class FailureTracker:
    def __init__(self, path: Path):
        self.path = Path(path)

    def count(self) -> int:
        if not self.path.exists():
            return 0
        try:
            return int(self.path.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            return 0

    def record_failure(self) -> None:
        n = self.count() + 1
        self.path.write_text(str(n), encoding="utf-8")

    def reset(self) -> None:
        self.path.write_text("0", encoding="utf-8")

    def should_alert(self, threshold: int = 3) -> bool:
        return self.count() >= threshold
```

- [ ] **Step 4: 跑測試確認通過**

```bash
pytest tests/test_intel_failure_tracker.py -v
```

Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add src/intel_failure_tracker.py tests/test_intel_failure_tracker.py
git commit -m "feat: add failure tracker for auto-intel pipeline"
```

---

## Task 3: intel_validator.py — JSON Schema 驗證 (TDD)

**責任：** 接收 Gemini 回傳的 JSON 字串，先做格式驗證。

**Files:**
- Test: `tests/test_intel_validator.py`
- Create: `src/intel_validator.py`

- [ ] **Step 1: 寫 schema 驗證的失敗測試**

Create `C:\Users\wenny\Desktop\WorkSpace\新聞看板\tests\test_intel_validator.py`：

```python
"""Unit tests for intel_validator."""
import pytest
from intel_validator import validate_schema, ValidationError


VALID_INTEL = {
    "edited_at": "2026-05-11T07:00:00+08:00",
    "edited_by": "ai-auto-v1",
    "thesis": "全球指數同步下跌，避險旋轉浮現",
    "top_3_events": [
        {"event": "澳洲 CPI 低於預期", "source": "CNBC", "implication": "降息預期升溫"},
        {"event": "OpenAI 估值修正", "source": "商業周刊", "implication": "AI 估值壓力"},
        {"event": "中東地緣升溫", "source": "BBC", "implication": "油價避險需求"},
    ],
    "why_it_matters": ["a", "b", "c"],
    "what_changed": ["a", "b", "c"],
    "cross_signals": ["a", "b", "c"],
    "section_signals": {
        "world": "→ a",
        "finance": "→ b",
        "crypto": "→ c",
        "tech": "→ d",
        "entertainment": "→ e",
    },
    "report_takeaways": {"Some Report": "key takeaway"},
}


def test_valid_intel_passes():
    validate_schema(VALID_INTEL)  # should not raise


def test_missing_thesis_fails():
    bad = {**VALID_INTEL}
    del bad["thesis"]
    with pytest.raises(ValidationError):
        validate_schema(bad)


def test_top_3_with_only_2_events_fails():
    bad = {**VALID_INTEL, "top_3_events": VALID_INTEL["top_3_events"][:2]}
    with pytest.raises(ValidationError):
        validate_schema(bad)


def test_section_signals_missing_key_fails():
    bad = {**VALID_INTEL, "section_signals": {"world": "→ a"}}
    with pytest.raises(ValidationError):
        validate_schema(bad)


def test_event_missing_implication_fails():
    bad = {**VALID_INTEL, "top_3_events": [
        {"event": "x", "source": "y"},  # missing implication
        VALID_INTEL["top_3_events"][1],
        VALID_INTEL["top_3_events"][2],
    ]}
    with pytest.raises(ValidationError):
        validate_schema(bad)
```

- [ ] **Step 2: 跑測試確認 fail**

```bash
pytest tests/test_intel_validator.py -v
```

Expected: `ModuleNotFoundError: No module named 'intel_validator'`

- [ ] **Step 3: 實作 schema 驗證**

Create `C:\Users\wenny\Desktop\WorkSpace\新聞看板\src\intel_validator.py`：

```python
"""驗證 AI 生成的 intel.json：格式、數字真實性、空泛詞。"""
import re
from jsonschema import Draft202012Validator


class ValidationError(Exception):
    pass


INTEL_SCHEMA = {
    "type": "object",
    "required": [
        "edited_at", "edited_by", "thesis", "top_3_events",
        "why_it_matters", "what_changed", "cross_signals",
        "section_signals", "report_takeaways",
    ],
    "properties": {
        "edited_at": {"type": "string"},
        "edited_by": {"type": "string"},
        "thesis": {"type": "string", "minLength": 10},
        "top_3_events": {
            "type": "array",
            "minItems": 3,
            "maxItems": 3,
            "items": {
                "type": "object",
                "required": ["event", "source", "implication"],
                "properties": {
                    "event": {"type": "string", "minLength": 5},
                    "source": {"type": "string", "minLength": 1},
                    "implication": {"type": "string", "minLength": 5},
                },
            },
        },
        "why_it_matters": {
            "type": "array",
            "minItems": 2,
            "items": {"type": "string", "minLength": 5},
        },
        "what_changed": {
            "type": "array",
            "minItems": 2,
            "items": {"type": "string", "minLength": 5},
        },
        "cross_signals": {
            "type": "array",
            "minItems": 2,
            "items": {"type": "string", "minLength": 5},
        },
        "section_signals": {
            "type": "object",
            "required": ["world", "finance", "crypto", "tech", "entertainment"],
            "properties": {
                "world": {"type": "string"},
                "finance": {"type": "string"},
                "crypto": {"type": "string"},
                "tech": {"type": "string"},
                "entertainment": {"type": "string"},
            },
        },
        "report_takeaways": {"type": "object"},
    },
}


def validate_schema(intel: dict) -> None:
    """Raise ValidationError if intel does not match schema."""
    validator = Draft202012Validator(INTEL_SCHEMA)
    errors = sorted(validator.iter_errors(intel), key=lambda e: e.path)
    if errors:
        msgs = "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:5])
        raise ValidationError(f"schema invalid: {msgs}")
```

- [ ] **Step 4: 跑測試確認通過**

```bash
pytest tests/test_intel_validator.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add src/intel_validator.py tests/test_intel_validator.py
git commit -m "feat: add JSON schema validation for intel"
```

---

## Task 4: intel_validator.py — 空泛詞掃描 (TDD)

**Files:**
- Modify: `tests/test_intel_validator.py`
- Modify: `src/intel_validator.py`

- [ ] **Step 1: 加空泛詞測試**

在 `C:\Users\wenny\Desktop\WorkSpace\新聞看板\tests\test_intel_validator.py` 結尾新增：

```python
from intel_validator import scan_banned_words


def test_no_banned_words_passes():
    scan_banned_words("台股 -0.86%，避險旋轉浮現")  # should not raise


def test_structural_word_fails():
    with pytest.raises(ValidationError):
        scan_banned_words("市場面臨結構性挑戰")


def test_continuous_word_fails():
    with pytest.raises(ValidationError):
        scan_banned_words("通膨壓力持續存在")


def test_long_term_growth_fails():
    with pytest.raises(ValidationError):
        scan_banned_words("產業呈現長期增長態勢")


def test_comprehensive_fails():
    with pytest.raises(ValidationError):
        scan_banned_words("全面性的下跌風險")


def test_banned_word_inside_intel_object():
    """The full-intel helper applies banned-word scan across all text fields."""
    from intel_validator import scan_intel_for_banned_words
    bad_intel = {**VALID_INTEL, "thesis": "市場面臨結構性挑戰"}
    with pytest.raises(ValidationError):
        scan_intel_for_banned_words(bad_intel)
```

- [ ] **Step 2: 跑測試確認 fail**

```bash
pytest tests/test_intel_validator.py -v
```

Expected: `ImportError: cannot import name 'scan_banned_words'`

- [ ] **Step 3: 實作空泛詞掃描**

在 `C:\Users\wenny\Desktop\WorkSpace\新聞看板\src\intel_validator.py` 結尾新增：

```python
BANNED_WORDS = [
    "結構性",
    "持續",
    "長期增長",
    "長期成長",
    "全面",
    "廣泛",
    "趨勢",
]


def scan_banned_words(text: str) -> None:
    """Raise ValidationError if text contains banned filler words."""
    for word in BANNED_WORDS:
        if word in text:
            raise ValidationError(f"banned word found: '{word}' in text")


def scan_intel_for_banned_words(intel: dict) -> None:
    """Recursively scan all string values in intel dict."""
    def walk(node):
        if isinstance(node, str):
            scan_banned_words(node)
        elif isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(intel)
```

- [ ] **Step 4: 跑測試確認通過**

```bash
pytest tests/test_intel_validator.py -v
```

Expected: `11 passed`

- [ ] **Step 5: Commit**

```bash
git add src/intel_validator.py tests/test_intel_validator.py
git commit -m "feat: add banned-word scan for intel anti-fluff"
```

---

## Task 5: intel_validator.py — 數字交叉驗證 (TDD)

**責任：** 抽取 intel 中出現的百分比與價格數字，比對 market.json / crypto.json 是否真有對應值。

**Files:**
- Modify: `tests/test_intel_validator.py`
- Modify: `src/intel_validator.py`

- [ ] **Step 1: 加數字交叉驗證測試**

在 `tests/test_intel_validator.py` 結尾新增：

```python
from intel_validator import extract_numbers, verify_numbers_against_source


def test_extract_percentages():
    nums = extract_numbers("台股 -0.86%、Nasdaq -0.90%、Dow +0.05%")
    assert {"-0.86%", "-0.90%", "+0.05%"} == set(nums["pct"])


def test_extract_prices():
    nums = extract_numbers("BTC $76,000、ETH $2,288")
    assert "$76,000" in nums["price"] and "$2,288" in nums["price"]


SAMPLE_MARKET = {
    "indices": [
        {"label": "台股加權", "price": 39521.73, "change_pct": -0.8612},
        {"label": "Nasdaq", "price": 21500.0, "change_pct": -0.9034},
    ]
}

SAMPLE_CRYPTO = {
    "coins": [
        {"id": "bitcoin", "price_usd": 76000, "change_24h_pct": -0.29},
        {"id": "ethereum", "price_usd": 2288, "change_24h_pct": 0.18},
    ]
}


def test_valid_pct_within_tolerance():
    """-0.86% 與來源 -0.8612 容忍 0.05pp 內，應通過。"""
    text = "台股 -0.86%、Nasdaq -0.90%"
    verify_numbers_against_source(text, SAMPLE_MARKET, SAMPLE_CRYPTO)


def test_hallucinated_pct_fails():
    """-9.99% 找不到對應，應 raise。"""
    with pytest.raises(ValidationError):
        verify_numbers_against_source(
            "台股 -9.99%", SAMPLE_MARKET, SAMPLE_CRYPTO
        )


def test_valid_btc_price_within_tolerance():
    """BTC $76,300 與來源 $76,000 在 0.5% 內，應通過。"""
    text = "BTC $76,300"
    verify_numbers_against_source(text, SAMPLE_MARKET, SAMPLE_CRYPTO)


def test_hallucinated_price_fails():
    with pytest.raises(ValidationError):
        verify_numbers_against_source(
            "BTC $99,999", SAMPLE_MARKET, SAMPLE_CRYPTO
        )
```

- [ ] **Step 2: 跑測試確認 fail**

```bash
pytest tests/test_intel_validator.py -v
```

Expected: `ImportError: cannot import name 'extract_numbers'`

- [ ] **Step 3: 實作數字交叉驗證**

在 `src/intel_validator.py` 結尾新增：

```python
PCT_RE = re.compile(r"[+-]?\d+\.\d{1,2}%")
PRICE_RE = re.compile(r"\$\d{1,3}(?:,\d{3})+|\$\d+")


def extract_numbers(text: str) -> dict:
    """Return {'pct': [...], 'price': [...]} of numbers found in text."""
    return {
        "pct": PCT_RE.findall(text),
        "price": PRICE_RE.findall(text),
    }


def _pct_to_float(s: str) -> float:
    return float(s.replace("%", ""))


def _price_to_float(s: str) -> float:
    return float(s.replace("$", "").replace(",", ""))


def _collect_source_pcts(market: dict, crypto: dict) -> list:
    out = []
    for idx in market.get("indices", []):
        if idx.get("change_pct") is not None:
            out.append(float(idx["change_pct"]))
    for c in crypto.get("coins", []):
        if c.get("change_24h_pct") is not None:
            out.append(float(c["change_24h_pct"]))
    return out


def _collect_source_prices(market: dict, crypto: dict) -> list:
    out = []
    for idx in market.get("indices", []):
        if idx.get("price") is not None:
            out.append(float(idx["price"]))
    for c in crypto.get("coins", []):
        if c.get("price_usd") is not None:
            out.append(float(c["price_usd"]))
    return out


def verify_numbers_against_source(
    text: str, market: dict, crypto: dict,
    pct_tolerance: float = 0.05,
    price_relative_tolerance: float = 0.005,
) -> None:
    """
    Raise ValidationError if any pct / price in text has no match in source data.
    pct_tolerance: absolute (e.g. 0.05 = 0.05 percentage point)
    price_relative_tolerance: relative (e.g. 0.005 = 0.5%)
    """
    nums = extract_numbers(text)
    source_pcts = _collect_source_pcts(market, crypto)
    source_prices = _collect_source_prices(market, crypto)

    for pct_str in nums["pct"]:
        target = _pct_to_float(pct_str)
        if not any(abs(target - sp) <= pct_tolerance for sp in source_pcts):
            raise ValidationError(
                f"hallucinated pct '{pct_str}' (no match within {pct_tolerance}pp of source data)"
            )

    for price_str in nums["price"]:
        target = _price_to_float(price_str)
        if not any(
            abs(target - sp) / max(sp, 1e-9) <= price_relative_tolerance
            for sp in source_prices
        ):
            raise ValidationError(
                f"hallucinated price '{price_str}' (no match within {price_relative_tolerance*100}% of source data)"
            )
```

- [ ] **Step 4: 跑測試確認通過**

```bash
pytest tests/test_intel_validator.py -v
```

Expected: `17 passed`

- [ ] **Step 5: Commit**

```bash
git add src/intel_validator.py tests/test_intel_validator.py
git commit -m "feat: add number cross-check to detect hallucinated stats"
```

---

## Task 6: intel_prompt.py — System Prompt 與輸入組裝

**責任：** 提供 system prompt 常數、few-shot 範例、把 news/market/crypto/reports 組裝成模型可讀的 user prompt。

**Files:**
- Test: `tests/test_intel_prompt.py`
- Create: `src/intel_prompt.py`

- [ ] **Step 1: 寫輸入組裝的測試**

Create `C:\Users\wenny\Desktop\WorkSpace\新聞看板\tests\test_intel_prompt.py`：

```python
"""Unit tests for intel_prompt input builder."""
from intel_prompt import build_user_prompt, SYSTEM_PROMPT, MODEL_NAME


def test_system_prompt_contains_iron_rules():
    """系統指令必須含核心規則關鍵字。"""
    assert "鐵則" in SYSTEM_PROMPT
    assert "禁用" in SYSTEM_PROMPT
    assert "→" in SYSTEM_PROMPT


def test_model_name_defined():
    assert MODEL_NAME.startswith("gemini")


def test_build_user_prompt_includes_all_sections():
    market = {"indices": [{"label": "台股", "price": 100, "change_pct": -0.5}]}
    crypto = {"coins": [{"id": "bitcoin", "price_usd": 70000, "change_24h_pct": 1.0}]}
    news = {"categories": {
        "world": [{"title": "T1", "source": "S1", "published": "2026-05-11"}],
        "finance": [{"title": "T2", "source": "S2", "published": "2026-05-11"}],
        "crypto": [],
        "tech": [],
        "entertainment": [],
    }}
    reports = {"items": [{"title": "R1", "source": "RS1"}]}

    prompt = build_user_prompt(market, crypto, news, reports, "2026-05-11T07:00:00+08:00")

    assert "台股" in prompt
    assert "bitcoin" in prompt
    assert "T1" in prompt
    assert "R1" in prompt
    assert "2026-05-11" in prompt


def test_build_user_prompt_limits_news_per_category():
    """每分類最多 8 條。"""
    news = {"categories": {
        "world": [{"title": f"T{i}", "source": "S", "published": "2026"} for i in range(20)],
        "finance": [], "crypto": [], "tech": [], "entertainment": [],
    }}
    prompt = build_user_prompt({}, {}, news, {}, "now")
    assert "T0" in prompt
    assert "T7" in prompt
    assert "T15" not in prompt
```

- [ ] **Step 2: 跑測試確認 fail**

```bash
pytest tests/test_intel_prompt.py -v
```

Expected: `ModuleNotFoundError: No module named 'intel_prompt'`

- [ ] **Step 3: 實作 intel_prompt.py**

Create `C:\Users\wenny\Desktop\WorkSpace\新聞看板\src\intel_prompt.py`：

```python
"""Gemini system prompt + user prompt builder for auto-intel generation."""
import json


MODEL_NAME = "gemini-2.5-flash"

SYSTEM_PROMPT = """你是新聞看板的資深市場觀察員。任務：根據今日抓取的新聞、市場、加密、機構報告數據，產出當日 intel.json。

# 鐵則（違反任何一條都視為失敗）

1. 引用強制：每一個結論必須能對應到輸入資料中的「具體新聞標題」或「具體數字」。
2. 禁用空泛詞:「結構性」、「持續」、「長期」、「全面」、「廣泛」、「趨勢」——除非你能引用至少 3 個獨立數據點支撐。
3. 禁止填空：輸入資料沒提到的事件、人物、數字,絕對不可寫入。
4. 數字精確:股市/匯率必須帶單位與漲跌幅(例如 "Nasdaq -0.90%");新聞引用必須帶來源名(例如 "(CNBC)")。
5. 風格：簡潔、因果用「→」連接、不寫修飾性形容詞、繁體中文。
6. 寧缺勿濫：若某欄位沒有足夠數據支撐,回傳空陣列 [] 或 null,不要硬填。

# 範例(學起來,輸出時模仿)

## 好 thesis
"全球同步修正、避險旋轉浮現；澳洲通膨意外走低,重新點燃降息預期"
為什麼好：兩個事件都對應輸入資料——指數同步下跌的具體數字 + 澳洲 CPI 新聞。

## 壞 thesis(不可這樣寫)
"市場面臨結構性挑戰,投資情緒謹慎,未來走向尚待觀察"
為什麼壞：「結構性」「謹慎」「尚待觀察」三個套話、無一條對應輸入資料。

## 好 cross_signal
"通膨 ↓ → 利率預期 ↓ → Nasdaq 中期估值利多 vs 短線壓力"

## 壞 cross_signal
"市場各環節相互影響,需要綜合考量。"

## 好 what_changed
"全球指數同步下跌:台股 -0.86%、Nasdaq -0.90%、日經 -1.02%、S&P -0.49%"

## 壞 what_changed
"市場呈現下跌格局,投資人情緒受影響"

# 輸出格式(純 JSON,不加任何前後說明文字,不加 markdown code fence)

{
  "edited_at": "<填入提供的時間戳>",
  "edited_by": "ai-auto-v1",
  "thesis": "string,30-50 字,必須引用至少一個輸入資料中的具體事件或數字",
  "top_3_events": [
    {"event": "...", "source": "...", "implication": "..."},
    {"event": "...", "source": "...", "implication": "..."},
    {"event": "...", "source": "...", "implication": "..."}
  ],
  "why_it_matters": ["3 點"],
  "what_changed": ["3-4 點,必須包含具體數字"],
  "cross_signals": ["3-4 條因果鏈,用 → 連接"],
  "section_signals": {
    "world": "→ ...",
    "finance": "→ ...",
    "crypto": "→ ...",
    "tech": "→ ...",
    "entertainment": "→ ..."
  },
  "report_takeaways": {"報告標題前綴": "一句重點"}
}

# 內部自我檢查(在輸出前完成,但不要把檢查過程寫進輸出)

- thesis 中每個事件能在 market_data 或 news_titles 找到嗎?
- top_3_events 的 implication 都帶具體數字嗎?
- what_changed 每行都有 % 或數字嗎?
- cross_signals 每條都提到具體資產嗎?
- 有任何「結構性 / 持續 / 長期 / 全面 / 廣泛 / 趨勢」嗎? 若有→重寫。
- report_takeaways 的 key 真的對應 reports 輸入中的標題前綴嗎?

通過全部檢查後才輸出 JSON。
"""

NEWS_TOP_N_PER_CATEGORY = 8
REPORTS_TOP_N = 10


def _trim_news(news: dict) -> dict:
    """Keep only top N titles per category, drop summaries / links."""
    out = {}
    cats = news.get("categories", {}) if isinstance(news, dict) else {}
    for cat, items in cats.items():
        out[cat] = [
            {"title": it.get("title", ""), "source": it.get("source", ""), "published": it.get("published", "")}
            for it in items[:NEWS_TOP_N_PER_CATEGORY]
        ]
    return out


def _trim_reports(reports: dict) -> list:
    items = reports.get("items", []) if isinstance(reports, dict) else []
    return [{"title": it.get("title", ""), "source": it.get("source", "")} for it in items[:REPORTS_TOP_N]]


def build_user_prompt(market: dict, crypto: dict, news: dict, reports: dict, timestamp: str) -> str:
    """Assemble the user-side prompt with all input data."""
    parts = [
        f"時間戳：{timestamp}",
        "",
        "## 市場數據(market.json)",
        json.dumps(market, ensure_ascii=False, indent=2),
        "",
        "## 加密數據(crypto.json)",
        json.dumps(crypto, ensure_ascii=False, indent=2),
        "",
        "## 新聞標題(各分類最多 Top 8)",
        json.dumps(_trim_news(news), ensure_ascii=False, indent=2),
        "",
        "## 機構報告(最多 10 篇)",
        json.dumps(_trim_reports(reports), ensure_ascii=False, indent=2),
        "",
        "請依照系統指令的格式輸出純 JSON。",
    ]
    return "\n".join(parts)
```

- [ ] **Step 4: 跑測試確認通過**

```bash
pytest tests/test_intel_prompt.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add src/intel_prompt.py tests/test_intel_prompt.py
git commit -m "feat: add system prompt + user prompt builder for Gemini"
```

---

## Task 7: generate_intel.py — 主協調流程

**責任：** 主腳本，協調以下事務：載入資料 → 檢查 override → 呼叫 Gemini → 驗證 → 寫檔 / 失敗處理。

**Files:**
- Test: `tests/test_generate_intel.py`
- Create: `src/generate_intel.py`

- [ ] **Step 1: 寫 generate_intel 的測試（mock Gemini）**

Create `C:\Users\wenny\Desktop\WorkSpace\新聞看板\tests\test_generate_intel.py`：

```python
"""Tests for generate_intel orchestration (Gemini client mocked)."""
import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

import generate_intel


@pytest.fixture
def fake_data_dir(tmp_path):
    """Create a tmp data dir with minimal news/market/crypto/reports JSON."""
    (tmp_path / "market.json").write_text(json.dumps({
        "indices": [{"label": "台股", "price": 39521.73, "change_pct": -0.86}]
    }, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "crypto.json").write_text(json.dumps({
        "coins": [{"id": "bitcoin", "price_usd": 76000, "change_24h_pct": -0.29}]
    }, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "news.json").write_text(json.dumps({
        "categories": {"world": [{"title": "X", "source": "S", "published": "2026"}],
                       "finance": [], "crypto": [], "tech": [], "entertainment": []}
    }, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "reports.json").write_text(json.dumps({"items": []}, ensure_ascii=False), encoding="utf-8")
    return tmp_path


VALID_GEMINI_OUTPUT = json.dumps({
    "edited_at": "2026-05-11T07:00:00+08:00",
    "edited_by": "ai-auto-v1",
    "thesis": "台股 -0.86% 領跌,避險旋轉浮現",
    "top_3_events": [
        {"event": "台股下跌", "source": "Yahoo", "implication": "資金外流 -0.86%"},
        {"event": "BTC 整理", "source": "CoinGecko", "implication": "加密觀望 BTC $76,000"},
        {"event": "新聞 X 發生", "source": "S", "implication": "影響 -0.86%"},
    ],
    "why_it_matters": ["a-0.86%", "b-0.86%"],
    "what_changed": ["台股 -0.86%", "BTC $76,000"],
    "cross_signals": ["跌 → 資金流出 → 台股 -0.86%", "BTC $76,000 觀望"],
    "section_signals": {
        "world": "→ X 事件影響", "finance": "→ 台股 -0.86%",
        "crypto": "→ BTC $76,000", "tech": "→ 觀望", "entertainment": "→ 平淡",
    },
    "report_takeaways": {},
})


def _make_mock_client(text_output: str):
    """Helper to build a Gemini client mock that returns the given text."""
    client = MagicMock()
    response = MagicMock()
    response.text = text_output
    client.models.generate_content.return_value = response
    return client


def test_override_skips_gemini(fake_data_dir):
    """如果 intel.override.json 存在,完全跳過 AI 呼叫。"""
    override = {"thesis": "manual override", "edited_by": "manual"}
    (fake_data_dir / "intel.override.json").write_text(
        json.dumps(override, ensure_ascii=False), encoding="utf-8"
    )

    mock_client = _make_mock_client("should not be called")
    result = generate_intel.run(data_dir=fake_data_dir, gemini_client=mock_client)

    assert result["status"] == "override"
    intel = json.loads((fake_data_dir / "intel.json").read_text(encoding="utf-8"))
    assert intel["thesis"] == "manual override"
    mock_client.models.generate_content.assert_not_called()


def test_success_writes_intel_and_resets_failures(fake_data_dir):
    (fake_data_dir / ".intel_failures").write_text("2", encoding="utf-8")
    mock_client = _make_mock_client(VALID_GEMINI_OUTPUT)

    result = generate_intel.run(data_dir=fake_data_dir, gemini_client=mock_client)

    assert result["status"] == "ok"
    intel = json.loads((fake_data_dir / "intel.json").read_text(encoding="utf-8"))
    assert "-0.86%" in intel["thesis"]
    assert (fake_data_dir / ".intel_failures").read_text(encoding="utf-8").strip() == "0"


def test_validation_failure_keeps_yesterday_and_increments_counter(fake_data_dir):
    """If output fails validation twice, keep old intel.json + increment counter."""
    # seed yesterday's intel
    yesterday = {"thesis": "yesterday", "edited_by": "manual"}
    (fake_data_dir / "intel.json").write_text(
        json.dumps(yesterday, ensure_ascii=False), encoding="utf-8"
    )

    bad_output = json.dumps({**json.loads(VALID_GEMINI_OUTPUT), "thesis": "市場結構性挑戰"})
    mock_client = _make_mock_client(bad_output)

    result = generate_intel.run(data_dir=fake_data_dir, gemini_client=mock_client)

    assert result["status"] == "failed"
    # yesterday's intel preserved
    intel = json.loads((fake_data_dir / "intel.json").read_text(encoding="utf-8"))
    assert intel["thesis"] == "yesterday"
    # counter incremented
    assert (fake_data_dir / ".intel_failures").read_text(encoding="utf-8").strip() == "1"
    # generate_content called twice (1 retry)
    assert mock_client.models.generate_content.call_count == 2


def test_gemini_api_exception_treated_as_failure(fake_data_dir):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("api down")

    result = generate_intel.run(data_dir=fake_data_dir, gemini_client=mock_client)

    assert result["status"] == "failed"


def test_strips_markdown_fence_from_gemini_output(fake_data_dir):
    """Gemini sometimes wraps JSON in ```json fences; we tolerate it."""
    fenced = f"```json\n{VALID_GEMINI_OUTPUT}\n```"
    mock_client = _make_mock_client(fenced)

    result = generate_intel.run(data_dir=fake_data_dir, gemini_client=mock_client)

    assert result["status"] == "ok"
```

- [ ] **Step 2: 跑測試確認 fail**

```bash
pytest tests/test_generate_intel.py -v
```

Expected: `ModuleNotFoundError: No module named 'generate_intel'`

- [ ] **Step 3: 實作 generate_intel.py**

Create `C:\Users\wenny\Desktop\WorkSpace\新聞看板\src\generate_intel.py`：

```python
"""主流程：呼叫 Gemini 產生 intel.json,含驗證、Override、失敗處理。"""
import os
import re
import sys
import json
import time
import shutil
import datetime as dt
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from intel_prompt import SYSTEM_PROMPT, MODEL_NAME, build_user_prompt
from intel_validator import (
    validate_schema,
    scan_intel_for_banned_words,
    verify_numbers_against_source,
    ValidationError,
)
from intel_failure_tracker import FailureTracker


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = ROOT / "data"
RETRY_COUNT = 1
FAILURE_THRESHOLD = 3


def _strip_code_fence(text: str) -> str:
    """Remove ```json ... ``` fences if Gemini wrapped output in markdown."""
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _now_tpe_iso() -> str:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec="seconds")


def _validate_full(intel: dict, market: dict, crypto: dict) -> None:
    validate_schema(intel)
    scan_intel_for_banned_words(intel)
    # Cross-check numbers across all string fields
    def walk(node):
        if isinstance(node, str):
            verify_numbers_against_source(node, market, crypto)
        elif isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(intel)


def _call_gemini(client, user_prompt: str) -> str:
    """Single Gemini call, returns raw text."""
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[{"role": "user", "parts": [{"text": user_prompt}]}],
        config={
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "temperature": 0.4,
        },
    )
    return response.text


def _try_generate(client, user_prompt: str, market: dict, crypto: dict) -> dict:
    """One attempt: call Gemini, parse, validate. Raise on any failure."""
    raw = _call_gemini(client, user_prompt)
    text = _strip_code_fence(raw)
    intel = json.loads(text)
    intel["edited_at"] = _now_tpe_iso()
    intel["edited_by"] = "ai-auto-v1"
    _validate_full(intel, market, crypto)
    return intel


def run(data_dir: Path = None, gemini_client=None) -> dict:
    """Main entry. Returns {'status': 'ok'|'override'|'failed', 'detail': str}."""
    data_dir = Path(data_dir or DEFAULT_DATA_DIR)
    tracker = FailureTracker(data_dir / ".intel_failures")

    # 1. Override path
    override_path = data_dir / "intel.override.json"
    if override_path.exists():
        shutil.copy(override_path, data_dir / "intel.json")
        print("[OVERRIDE] 使用 intel.override.json,跳過 AI 生成")
        tracker.reset()
        return {"status": "override", "detail": "override file present"}

    # 2. Load inputs
    market = _load_json(data_dir / "market.json")
    crypto = _load_json(data_dir / "crypto.json")
    news = _load_json(data_dir / "news.json")
    reports = _load_json(data_dir / "reports.json")

    user_prompt = build_user_prompt(market, crypto, news, reports, _now_tpe_iso())

    # 3. Try + retry once on failure
    last_error = None
    for attempt in range(1 + RETRY_COUNT):
        try:
            intel = _try_generate(gemini_client, user_prompt, market, crypto)
            (data_dir / "intel.json").write_text(
                json.dumps(intel, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"[OK] intel.json 已更新(attempt {attempt + 1})")
            tracker.reset()
            return {"status": "ok", "detail": f"generated on attempt {attempt + 1}"}
        except (ValidationError, json.JSONDecodeError, RuntimeError, Exception) as e:
            last_error = e
            print(f"[RETRY] attempt {attempt + 1} 失敗:{type(e).__name__}: {e}")
            if attempt < RETRY_COUNT:
                time.sleep(5)

    # 4. Final failure
    tracker.record_failure()
    print(f"[FAIL] 保留昨日 intel.json,連續失敗 {tracker.count()} 次。最後錯誤:{last_error}")

    if tracker.should_alert(threshold=FAILURE_THRESHOLD):
        print(f"[ALERT] 連續失敗達 {FAILURE_THRESHOLD} 次,應發送 Telegram 警報")

    return {"status": "failed", "detail": str(last_error)}


def _build_real_client():
    """Lazy import google-genai only when actually running."""
    from google import genai
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("缺少 GEMINI_API_KEY 環境變數")
    return genai.Client(api_key=api_key)


def main():
    client = _build_real_client()
    result = run(gemini_client=client)
    print(f"\n結果:{result}")
    # Exit 0 even on 'failed' so pipeline continues (build_dashboard 仍要跑)
    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 跑測試確認通過**

```bash
pytest tests/test_generate_intel.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add src/generate_intel.py tests/test_generate_intel.py
git commit -m "feat: add generate_intel orchestration with override + retry + failure handling"
```

---

## Task 8: 整合 Telegram 警報

**責任：** 當連續失敗達 3 次時,實際發送 Telegram 警報訊息(目前 Task 7 只 print log,沒實際發送)。

**Files:**
- Modify: `src/generate_intel.py`
- Modify: `tests/test_generate_intel.py`

- [ ] **Step 1: 寫警報觸發的測試**

在 `tests/test_generate_intel.py` 加入：

```python
def test_alert_sent_on_third_consecutive_failure(fake_data_dir, monkeypatch):
    """連續第 3 次失敗時呼叫 telegram alert function。"""
    (fake_data_dir / ".intel_failures").write_text("2", encoding="utf-8")  # 已經 2 次

    bad_output = json.dumps({**json.loads(VALID_GEMINI_OUTPUT), "thesis": "市場結構性挑戰"})
    mock_client = _make_mock_client(bad_output)

    alert_calls = []
    monkeypatch.setattr(generate_intel, "_send_alert", lambda msg: alert_calls.append(msg))

    result = generate_intel.run(data_dir=fake_data_dir, gemini_client=mock_client)

    assert result["status"] == "failed"
    assert len(alert_calls) == 1
    assert "3" in alert_calls[0]
    # alert sent 後,counter 應被 reset 為 0(避免每次都發)
    assert (fake_data_dir / ".intel_failures").read_text(encoding="utf-8").strip() == "0"


def test_alert_not_sent_below_threshold(fake_data_dir, monkeypatch):
    """連續第 1 次失敗時不發警報。"""
    bad_output = json.dumps({**json.loads(VALID_GEMINI_OUTPUT), "thesis": "市場結構性挑戰"})
    mock_client = _make_mock_client(bad_output)

    alert_calls = []
    monkeypatch.setattr(generate_intel, "_send_alert", lambda msg: alert_calls.append(msg))

    generate_intel.run(data_dir=fake_data_dir, gemini_client=mock_client)

    assert len(alert_calls) == 0
```

- [ ] **Step 2: 跑測試確認 fail**

```bash
pytest tests/test_generate_intel.py -v -k alert
```

Expected: `AttributeError: module 'generate_intel' has no attribute '_send_alert'`

- [ ] **Step 3: 實作 _send_alert 與整合**

在 `src/generate_intel.py` 中,在 `run()` 函式之前新增 `_send_alert`：

```python
def _send_alert(message: str) -> None:
    """Send Telegram alert. Silent no-op if creds missing (e.g. local testing)."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print(f"[ALERT-SKIP] 缺少 Telegram 憑證,警報未送出:{message}")
        return
    import requests
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=10)
        print(f"[ALERT-SENT] {message}")
    except Exception as e:
        print(f"[ALERT-ERROR] {e}")
```

並修改 `run()` 中的失敗末段:

替換原本：
```python
    if tracker.should_alert(threshold=FAILURE_THRESHOLD):
        print(f"[ALERT] 連續失敗達 {FAILURE_THRESHOLD} 次,應發送 Telegram 警報")
```

為：
```python
    if tracker.should_alert(threshold=FAILURE_THRESHOLD):
        _send_alert(f"⚠️ 新聞看板 AI Intel 已連續失敗 {tracker.count()} 次。請檢查 GitHub Actions log。")
        tracker.reset()
```

- [ ] **Step 4: 跑測試確認通過**

```bash
pytest tests/test_generate_intel.py -v
```

Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add src/generate_intel.py tests/test_generate_intel.py
git commit -m "feat: send Telegram alert on 3 consecutive intel failures"
```

---

## Task 9: 整合進 run_all.py

**Files:**
- Modify: `src/run_all.py`

- [ ] **Step 1: 修改 SCRIPTS list**

讀現有 `C:\Users\wenny\Desktop\WorkSpace\新聞看板\src\run_all.py`,將：

```python
SCRIPTS = ["fetch_news.py", "fetch_crypto.py", "fetch_market.py", "fetch_reports.py", "build_dashboard.py"]
```

改為：

```python
SCRIPTS = [
    "fetch_news.py",
    "fetch_crypto.py",
    "fetch_market.py",
    "fetch_reports.py",
    "generate_intel.py",
    "build_dashboard.py",
]
```

- [ ] **Step 2: 手動驗證(暫不真實呼叫 Gemini)**

由於 `GEMINI_API_KEY` 未設定時 `generate_intel.py` 會 raise,先確認其他 scripts 不受影響：

```bash
cd C:\Users\wenny\Desktop\WorkSpace\新聞看板\src
$env:GEMINI_API_KEY=""  # 確認空
python run_all.py
```

Expected：除了 `generate_intel.py` 報「缺少 GEMINI_API_KEY」之外,其他都 ok。`build_dashboard.py` 仍會跑(因為 generate_intel exit 0)。

注意:目前 generate_intel `main()` 會 `_build_real_client()` 失敗時 raise——這會讓 subprocess 收到 non-zero exit code,進而被 run_all.py 列為「失敗」。先接受此行為,Task 10 設定 Secret 後就會通。

- [ ] **Step 3: Commit**

```bash
git add src/run_all.py
git commit -m "chore: insert generate_intel into run_all pipeline"
```

---

## Task 10: GitHub Actions workflow 更新

**Files:**
- Modify: `.github/workflows/update.yml`

- [ ] **Step 1: 加入 GEMINI_API_KEY 環境變數**

讀現有 `C:\Users\wenny\Desktop\WorkSpace\新聞看板\.github\workflows\update.yml`,找到 `- name: Run pipeline` 步驟,將：

```yaml
      - name: Run pipeline
        working-directory: src
        run: python run_all.py
```

改為：

```yaml
      - name: Run pipeline
        working-directory: src
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python run_all.py
```

注意：`TELEGRAM_*` 也傳給 pipeline,讓 `generate_intel._send_alert` 在連續失敗時能呼叫 Telegram API。

- [ ] **Step 2: 修改 commit & push step,讓 .intel_failures 也 commit**

找到 `- name: Commit & push if changed` 步驟,將：

```yaml
          git add data/ dashboard/index.html
```

確認這行就會包含 `.intel_failures`(因為它在 `data/` 下),不需修改。但 `.gitignore` 不可排除此檔。

讀現有 `C:\Users\wenny\Desktop\WorkSpace\新聞看板\.gitignore` 確認:

```bash
cd C:\Users\wenny\Desktop\WorkSpace\新聞看板
type .gitignore
```

若有 `.intel_failures` 被排除,刪除該行。若沒有,跳過此 step。

- [ ] **Step 3: Commit workflow 修改**

```bash
git add .github/workflows/update.yml
git commit -m "ci: pass GEMINI_API_KEY and Telegram secrets to pipeline"
```

---

## Task 11: 跑全部測試,確認 regression-free

- [ ] **Step 1: 全測試**

```bash
cd C:\Users\wenny\Desktop\WorkSpace\新聞看板
pytest -v
```

Expected: `~24 passed`(failure_tracker 7 + validator 17 + prompt 4 + generate 7 = 35,實際數字依測試細節微調)

- [ ] **Step 2: 若有失敗,修正後重跑**

修正範圍限本 plan 的檔案。不要去動 `fetch_*.py` / `build_dashboard.py`。

---

## Task 12: 本機 dry-run 真實 Gemini 測試

**前置：** 至 [aistudio.google.com](https://aistudio.google.com/) 申請免費 API key。

- [ ] **Step 1: 設定環境變數**

PowerShell：
```powershell
$env:GEMINI_API_KEY = "<貼上你申請的 key>"
```

- [ ] **Step 2: 確保 data/*.json 是新的(否則 Gemini 看到的是舊新聞)**

```bash
cd C:\Users\wenny\Desktop\WorkSpace\新聞看板\src
python fetch_news.py
python fetch_crypto.py
python fetch_market.py
python fetch_reports.py
```

- [ ] **Step 3: 真實呼叫 Gemini 一次**

```bash
cd C:\Users\wenny\Desktop\WorkSpace\新聞看板\src
python generate_intel.py
```

Expected: `[OK] intel.json 已更新` + 印出 `結果:{'status': 'ok', ...}`

- [ ] **Step 4: 人工檢查產出**

打開 `data/intel.json`,逐欄位看：
- thesis 是否具體(含至少一個事件 + 數字)?
- top_3 implication 是否帶數字?
- cross_signals 是否真的用 `→` 連接、提具體資產?
- 是否有「結構性 / 持續 / 長期 / 全面」?(理論上會被擋下,出現即代表 prompt 漏洞)

若品質不到位:
- 紀錄哪幾個欄位空洞,在 `intel_prompt.SYSTEM_PROMPT` 加新 few-shot 範例
- 重跑 Task 12 Step 3

- [ ] **Step 5: 重 build dashboard 確認視覺正常**

```bash
python build_dashboard.py
```

打開 `dashboard/index.html`,確認「🧠 今日洞察」區塊顯示新內容。

- [ ] **Step 6: Commit 整批產出**

```bash
cd C:\Users\wenny\Desktop\WorkSpace\新聞看板
git add data/intel.json dashboard/index.html
git commit -m "test: first successful auto-intel generation"
```

---

## Task 13: GitHub Secret 設定 + 整合測試

- [ ] **Step 1: 在 GitHub repo 設定 Secret**

1. 開啟 `https://github.com/Winnie3721/news-dashboard/settings/secrets/actions`
2. 點 `New repository secret`
3. Name: `GEMINI_API_KEY`,Value: 申請到的 key
4. 點 `Add secret`

- [ ] **Step 2: Push 全部修改到 GitHub**

```bash
cd C:\Users\wenny\Desktop\WorkSpace\新聞看板
git push
```

- [ ] **Step 3: 手動觸發 workflow**

1. 開啟 `https://github.com/Winnie3721/news-dashboard/actions`
2. 左側點 `Auto Update Dashboard`
3. 右上角 `Run workflow` → `Run workflow`
4. 等 2-5 分鐘

- [ ] **Step 4: 檢查 log**

點進剛跑的 workflow → 看 `Run pipeline` 步驟。

Expected：log 中有 `[OK] intel.json 已更新`。

若有失敗（`[FAIL]`）：依 log 訊息修正 prompt 或 validator,重跑 Task 12 dry-run,push 後再觸發。

- [ ] **Step 5: 檢查線上 Dashboard**

開啟 `https://winnie3721.github.io/news-dashboard/`,確認「🧠 今日洞察」反映剛剛 Gemini 生成的內容。

可能需要等 GitHub Pages 部署 1-2 分鐘。

---

## Task 14: Override 機制驗證

- [ ] **Step 1: 建立 override 檔案**

在線上 GitHub 直接編輯:`https://github.com/Winnie3721/news-dashboard/new/main/data`,檔名 `intel.override.json`,內容：

```json
{
  "edited_at": "2026-05-11T12:00:00+08:00",
  "edited_by": "manual",
  "thesis": "(Override 測試)鮪魚手動接管今日洞察",
  "top_3_events": [
    {"event": "測試 1", "source": "manual", "implication": "驗證 override 生效"},
    {"event": "測試 2", "source": "manual", "implication": "驗證 override 生效"},
    {"event": "測試 3", "source": "manual", "implication": "驗證 override 生效"}
  ],
  "why_it_matters": ["a", "b"],
  "what_changed": ["a", "b"],
  "cross_signals": ["a", "b"],
  "section_signals": {"world": "→ a", "finance": "→ b", "crypto": "→ c", "tech": "→ d", "entertainment": "→ e"},
  "report_takeaways": {}
}
```

Commit 此檔。

- [ ] **Step 2: 手動觸發 workflow**

同 Task 13 Step 3。

- [ ] **Step 3: 檢查 log**

Expected：`Run pipeline` step 的 generate_intel 部分有 `[OVERRIDE] 使用 intel.override.json`,且不應有 Gemini API 呼叫。

- [ ] **Step 4: 檢查線上 Dashboard**

thesis 應顯示「(Override 測試)鮪魚手動接管今日洞察」。

- [ ] **Step 5: 刪除 override,恢復自動**

線上 GitHub 刪除 `data/intel.override.json`。下次 workflow 跑就會回 AI 模式。

---

## Task 15: 文件更新

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 更新 v0.1 範圍 / 已知限制章節**

讀 `C:\Users\wenny\Desktop\WorkSpace\新聞看板\README.md`,找到 `## 📅 v0.1 範圍` 章節,將：

```
- ❌ AI 摘要（待 Claude API key）
```

改為：

```
- ✅ AI 自動生成 Intelligence Layer（Gemini 2.5 Flash 免費額度）
```

並在「常見操作」章節加入新段落：

```markdown
### 想暫時手動接管「今日洞察」
建立 `data/intel.override.json`(schema 同 intel.json),AI 會自動跳過。
用完刪掉此檔即恢復自動。
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README v0.2 — AI intel auto-generation shipped"
```

---

## Task 16: 更新記憶檔

**Files:**
- Modify: `C:\Users\wenny\.claude\projects\C--Users-wenny-Desktop-WorkSpace\memory\project_news_dashboard.md`

- [ ] **Step 1: 更新「已完成 vs 待辦」清單**

將 `❌ AI 摘要(待 Claude API key)` 改為 `✅ AI 自動生成 intel.json(Gemini 2.5 Flash 免費額度)`,並新增說明 override 機制與失敗處理。

不需 commit(這是 ~/.claude 下的記憶檔,非 repo 內容)。

---

## Self-Review

✅ **Spec coverage:**
- §1 背景與目標 → Task 1–15 整體達成
- §2 系統架構 → Tasks 7, 9, 10 實作
- §3 Prompt 設計 → Task 6 完整實作 prompt 與 few-shot
- §4 驗證層 → Tasks 3, 4, 5 完整實作 schema / banned-words / number cross-check
- §5 Override 機制 → Task 7 (test) + Task 14 (整合驗證)
- §6 失敗處理 → Task 2 (tracker) + Task 7 (orchestration) + Task 8 (alert)
- §7 環境變數 → Task 10 + Task 13
- §9 測試策略 → Tasks 2–8 (TDD) + Tasks 11–14 (整合)
- §10 上線後監控 → Task 12 Step 4 + Task 13 Step 4(品質 manual check)
- §11 未來擴充 → 明確排除,不在本 plan 範圍

✅ **No placeholders:** 每個 step 都有完整 code 或具體指令。

✅ **Type consistency:** `FailureTracker`、`ValidationError`、`SYSTEM_PROMPT`、`MODEL_NAME`、`run()` 簽名一致。

⚠️ **One known gap:** Task 7 的測試 `test_validation_failure_keeps_yesterday_and_increments_counter` 依賴 banned word `結構性` 觸發 fail,這也是 Task 4 的測試前提。執行順序上依賴 Task 4 已實作。Plan 順序正確。

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-11-auto-intel-generation.md`.
