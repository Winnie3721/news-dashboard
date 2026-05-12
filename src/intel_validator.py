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
