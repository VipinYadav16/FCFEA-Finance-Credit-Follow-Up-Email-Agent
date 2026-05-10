from app.ai.sanitization import normalize_whitespace, sanitize_generated_output_text


def test_normalize_whitespace_removes_excess_spacing() -> None:
    value = "Hello   team\r\n\r\n\r\nPlease\treview."
    normalized = normalize_whitespace(value)
    assert normalized == "Hello team\n\nPlease review."


def test_sanitize_generated_output_text_enforces_max_len() -> None:
    value = "A" * 20
    assert len(sanitize_generated_output_text(value, max_len=10)) == 10
