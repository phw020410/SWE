import re
from urllib.parse import urlsplit

PATTERNS = [r"(?<!\d)\d{6}[- ]?[1-4]\d{6}(?!\d)", r"(?<!\d)01[016789][- .]?\d{3,4}[- .]?\d{4}(?!\d)",
            r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"]


def mask(text: str) -> str:
    for pattern in PATTERNS:
        text = re.sub(pattern, "[개인정보 가림]", text)
    return text


def mask_tree(value):
    if isinstance(value, str):
        return mask(value)
    if isinstance(value, list):
        return [mask_tree(x) for x in value]
    if isinstance(value, dict):
        return {k: mask_tree(v) for k, v in value.items()}
    return value


def safe_url(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme in {"http", "https"} and parsed.hostname and not parsed.username and not parsed.password else None
    except ValueError:
        return None


def md_text(value) -> str:
    # 외부 데이터가 Markdown 링크/HTML 구문으로 동작하지 않도록 이스케이프한다.
    value = str(value or "확인되지 않음").replace("\n", " ")
    return re.sub(r"([\\`*_{}\[\]<>|])", r"\\\1", value)
