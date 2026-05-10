import re


def normalize_whitespace(value: str) -> str:
    cleaned = value.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def sanitize_generated_output_text(value: str, max_len: int) -> str:
    normalized = normalize_whitespace(value)
    if len(normalized) > max_len:
        return normalized[:max_len].rstrip()
    return normalized
