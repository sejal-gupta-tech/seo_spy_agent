import ipaddress
import re
from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    normalized = url.strip()
    if normalized and not normalized.startswith(("http://", "https://")):
        normalized = f"https://{normalized}"
    return normalized


def is_valid_url(url: str) -> bool:
    parsed = urlparse(normalize_url(url))
    if parsed.scheme not in {"http", "https"}:
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    if hostname == "localhost":
        return True

    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        pass

    normalized_host = hostname.rstrip(".")
    labels = normalized_host.split(".")

    if len(labels) < 2:
        return False

    label_pattern = re.compile(r"^[A-Za-z0-9-]{1,63}$")
    if any(
        not label_pattern.fullmatch(label)
        or label.startswith("-")
        or label.endswith("-")
        for label in labels
    ):
        return False

    return not labels[-1].isdigit()
