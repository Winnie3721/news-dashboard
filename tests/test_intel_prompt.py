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
