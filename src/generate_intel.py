"""主流程:呼叫 Gemini 產生 intel.json,含驗證、Override、失敗處理。"""
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


def run(data_dir: Path = None, gemini_client=None) -> dict:
    """Main entry. Returns {'status': 'ok'|'override'|'failed', 'detail': str}."""
    data_dir = Path(data_dir or DEFAULT_DATA_DIR)
    tracker = FailureTracker(data_dir / ".intel_failures")

    # 1. Override path
    override_path = data_dir / "intel.override.json"
    if override_path.exists():
        try:
            override_data = json.loads(override_path.read_text(encoding="utf-8"))
            validate_schema(override_data)
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"[OVERRIDE-ERROR] intel.override.json 格式錯誤,忽略 override 並改走 AI 流程:{e}")
        else:
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
            print(f"[OK] intel.json 已更新 (attempt {attempt + 1})")
            tracker.reset()
            return {"status": "ok", "detail": f"generated on attempt {attempt + 1}"}
        except Exception as e:
            # Catches: ValidationError (validation), JSONDecodeError (bad Gemini output),
            # RuntimeError (Gemini API failures), and any unexpected SDK exception.
            # Does NOT catch SystemExit / KeyboardInterrupt (those inherit from BaseException).
            last_error = e
            print(f"[RETRY] attempt {attempt + 1} 失敗:{type(e).__name__}: {e}")
            if attempt < RETRY_COUNT:
                time.sleep(5)

    # 4. Final failure
    tracker.record_failure()
    print(f"[FAIL] 保留昨日 intel.json,連續失敗 {tracker.count()} 次。最後錯誤:{last_error}")

    if tracker.should_alert(threshold=FAILURE_THRESHOLD):
        _send_alert(f"⚠️ 新聞看板 AI Intel 已連續失敗 {tracker.count()} 次。請檢查 GitHub Actions log。")
        tracker.reset()

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
