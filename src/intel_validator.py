"""驗證 AI 生成的 intel.json:格式、數字真實性、空泛詞。"""
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
        # Note: minLength=1 (not 5) for the three list fields below is intentional.
        # Schema validates STRUCTURE only. Semantic quality (no fluff words, real
        # numbers, factual grounding) is enforced by scan_banned_words() and
        # verify_numbers_against_source() in this same module (added in Tasks 4-5).
        "why_it_matters": {
            "type": "array",
            "minItems": 2,
            "items": {"type": "string", "minLength": 1},
        },
        "what_changed": {
            "type": "array",
            "minItems": 2,
            "items": {"type": "string", "minLength": 1},
        },
        "cross_signals": {
            "type": "array",
            "minItems": 2,
            "items": {"type": "string", "minLength": 1},
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


BANNED_WORDS = [
    "結構性",
    "持續關注",
    "持續觀察",
    "持續發酵",
    "持續走強",
    "持續走弱",
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


PCT_RE = re.compile(r"[+-]?\d+(?:\.\d+)?%")
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
