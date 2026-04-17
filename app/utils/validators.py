from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    normalized = url.strip()
    if normalized and not normalized.startswith(("http://", "https://")):
        normalized = f"https://{normalized}"
    return normalized


def is_valid_url(url: str) -> bool:
    parsed = urlparse(normalize_url(url))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
