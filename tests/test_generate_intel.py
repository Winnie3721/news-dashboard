"""Tests for generate_intel orchestration (Gemini client mocked)."""
import json
import pytest
from unittest.mock import MagicMock
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
        {"event": "台股指數下跌", "source": "Yahoo", "implication": "資金外流 -0.86%"},
        {"event": "BTC 整理觀望", "source": "CoinGecko", "implication": "加密觀望 BTC $76,000"},
        {"event": "新聞 X 事件發生", "source": "S", "implication": "影響 -0.86%"},
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
    """如果 intel.override.json 存在且格式正確,完全跳過 AI 呼叫。"""
    # Must use a schema-valid override so the new validation lets it through
    override = json.loads(VALID_GEMINI_OUTPUT)
    override["thesis"] = "manual override 台股 -0.86% 人工覆寫"
    (fake_data_dir / "intel.override.json").write_text(
        json.dumps(override, ensure_ascii=False), encoding="utf-8"
    )

    mock_client = _make_mock_client("should not be called")
    result = generate_intel.run(data_dir=fake_data_dir, gemini_client=mock_client)

    assert result["status"] == "override"
    intel = json.loads((fake_data_dir / "intel.json").read_text(encoding="utf-8"))
    assert intel["thesis"] == "manual override 台股 -0.86% 人工覆寫"
    mock_client.models.generate_content.assert_not_called()


def test_success_writes_intel_and_resets_failures(fake_data_dir):
    (fake_data_dir / ".intel_failures").write_text("2", encoding="utf-8")
    mock_client = _make_mock_client(VALID_GEMINI_OUTPUT)

    result = generate_intel.run(data_dir=fake_data_dir, gemini_client=mock_client)

    assert result["status"] == "ok"
    intel = json.loads((fake_data_dir / "intel.json").read_text(encoding="utf-8"))
    assert "-0.86%" in intel["thesis"]
    assert (fake_data_dir / ".intel_failures").read_text(encoding="utf-8").strip() == "0"


def test_validation_failure_keeps_yesterday_and_increments_counter(fake_data_dir, monkeypatch):
    """If output fails validation twice, keep old intel.json + increment counter."""
    monkeypatch.setattr(generate_intel.time, "sleep", lambda _: None)
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


def test_gemini_api_exception_treated_as_failure(fake_data_dir, monkeypatch):
    monkeypatch.setattr(generate_intel.time, "sleep", lambda _: None)
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


def test_malformed_override_falls_through_to_ai(fake_data_dir, monkeypatch):
    """An override file with bad JSON should be ignored and AI flow runs."""
    monkeypatch.setattr(generate_intel.time, "sleep", lambda _: None)
    # Write malformed JSON as override
    (fake_data_dir / "intel.override.json").write_text("{ this is not valid json", encoding="utf-8")
    mock_client = _make_mock_client(VALID_GEMINI_OUTPUT)

    result = generate_intel.run(data_dir=fake_data_dir, gemini_client=mock_client)

    # AI was actually called because override was rejected
    assert result["status"] == "ok"
    mock_client.models.generate_content.assert_called()


def test_override_with_invalid_schema_falls_through_to_ai(fake_data_dir, monkeypatch):
    """Valid JSON but missing required intel fields → reject, fall through."""
    monkeypatch.setattr(generate_intel.time, "sleep", lambda _: None)
    # Write valid JSON but missing required fields like thesis, top_3_events
    (fake_data_dir / "intel.override.json").write_text(
        json.dumps({"some_field": "value"}, ensure_ascii=False), encoding="utf-8"
    )
    mock_client = _make_mock_client(VALID_GEMINI_OUTPUT)

    result = generate_intel.run(data_dir=fake_data_dir, gemini_client=mock_client)

    assert result["status"] == "ok"
    mock_client.models.generate_content.assert_called()


def test_alert_sent_on_third_consecutive_failure(fake_data_dir, monkeypatch):
    """連續第 3 次失敗時呼叫 telegram alert function。"""
    monkeypatch.setattr(generate_intel.time, "sleep", lambda _: None)
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
    monkeypatch.setattr(generate_intel.time, "sleep", lambda _: None)
    bad_output = json.dumps({**json.loads(VALID_GEMINI_OUTPUT), "thesis": "市場結構性挑戰"})
    mock_client = _make_mock_client(bad_output)

    alert_calls = []
    monkeypatch.setattr(generate_intel, "_send_alert", lambda msg: alert_calls.append(msg))

    generate_intel.run(data_dir=fake_data_dir, gemini_client=mock_client)

    assert len(alert_calls) == 0
