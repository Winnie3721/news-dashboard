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


from intel_validator import scan_banned_words


def test_no_banned_words_passes():
    scan_banned_words("台股 -0.86%,避險旋轉浮現")  # should not raise


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
    """-0.86% 與來源 -0.8612 容忍 0.05pp 內,應通過。"""
    text = "台股 -0.86%、Nasdaq -0.90%"
    verify_numbers_against_source(text, SAMPLE_MARKET, SAMPLE_CRYPTO)


def test_hallucinated_pct_fails():
    """-9.99% 找不到對應,應 raise。"""
    with pytest.raises(ValidationError):
        verify_numbers_against_source(
            "台股 -9.99%", SAMPLE_MARKET, SAMPLE_CRYPTO
        )


def test_valid_btc_price_within_tolerance():
    """BTC $76,300 與來源 $76,000 在 0.5% 內,應通過。"""
    text = "BTC $76,300"
    verify_numbers_against_source(text, SAMPLE_MARKET, SAMPLE_CRYPTO)


def test_hallucinated_price_fails():
    with pytest.raises(ValidationError):
        verify_numbers_against_source(
            "BTC $99,999", SAMPLE_MARKET, SAMPLE_CRYPTO
        )


def test_extract_integer_percentages():
    """Integer percentages without decimal point are also extracted."""
    nums = extract_numbers("市場 +5%、加密 -3%")
    assert "+5%" in nums["pct"]
    assert "-3%" in nums["pct"]


def test_extract_high_precision_percentages():
    """Percentages with >2 decimals also extracted (real market data has these)."""
    nums = extract_numbers("台股 -0.8612%、Nasdaq -0.9034%")
    assert "-0.8612%" in nums["pct"]
    assert "-0.9034%" in nums["pct"]


def test_hallucinated_integer_pct_fails():
    """Integer percentage hallucination should also be caught."""
    with pytest.raises(ValidationError):
        verify_numbers_against_source(
            "台股 -50%", SAMPLE_MARKET, SAMPLE_CRYPTO
        )
