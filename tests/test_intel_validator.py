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
