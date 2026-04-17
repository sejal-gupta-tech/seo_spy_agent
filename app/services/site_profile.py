import re
from collections import Counter
from urllib.parse import urlparse

from app.core.config import (
    DEFAULT_COMPANY_NAME,
    DEFAULT_MARKET_FOCUS_KEYWORDS,
    DEFAULT_REPORT_AUDIENCE,
    DEFAULT_SERVICE_PILLARS,
)

PROFILE_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "your",
    "from",
    "into",
    "about",
    "our",
    "you",
    "are",
    "how",
    "why",
    "what",
    "when",
    "where",
    "which",
    "can",
    "will",
    "all",
    "best",
    "more",
    "than",
    "services",
    "service",
    "solutions",
    "solution",
    "home",
    "official",
}

COMPOUND_TLDS = {"co", "com", "org", "net", "gov", "edu", "ac"}
TITLE_SEPARATOR_PATTERN = r"\s*[|:\-\u2013\u2014]\s*"


def _dedupe_preserving_order(values: list[str], limit: int) -> list[str]:
    seen = set()
    deduped = []

    for value in values:
        cleaned_value = " ".join(str(value).split()).strip(" -|:")
        if not cleaned_value:
            continue

        normalized_value = cleaned_value.lower()
        if normalized_value in seen:
            continue

        seen.add(normalized_value)
        deduped.append(cleaned_value)

        if len(deduped) >= limit:
            break

    return deduped


def _registrable_domain_label(url: str) -> str:
    netloc = urlparse(url).netloc.lower().split(":")[0]
    parts = [part for part in netloc.split(".") if part and part != "www"]

    if not parts:
        return DEFAULT_COMPANY_NAME

    if len(parts) >= 3 and len(parts[-1]) == 2 and parts[-2] in COMPOUND_TLDS:
        return parts[-3]

    if len(parts) >= 2:
        return parts[-2]

    return parts[0]


def _extract_company_name(url: str, title: str) -> str:
    domain_label = _registrable_domain_label(url)
    normalized_domain = re.sub(r"[^a-z0-9]+", "", domain_label.lower())
    title_parts = [
        part.strip()
        for part in re.split(TITLE_SEPARATOR_PATTERN, title or "")
        if part.strip()
    ]

    for part in title_parts:
        normalized_part = re.sub(r"[^a-z0-9]+", "", part.lower())
        if normalized_domain and normalized_domain in normalized_part:
            return part

    concise_parts = [part for part in title_parts if len(part.split()) <= 6]
    if concise_parts:
        return concise_parts[-1]

    if title_parts:
        return title_parts[0]

    return domain_label.replace("-", " ").title() or DEFAULT_COMPANY_NAME


def _extract_focus_terms(scraped_data: dict, ai_result: dict) -> list[str]:
    candidate_phrases = []
    title = scraped_data.get("title", "")
    description = scraped_data.get("description", "")
    headings = scraped_data.get("headings", {})
    ai_keywords = (
        ai_result.get("keywords", [])
        if isinstance(ai_result.get("keywords", []), list)
        else []
    )

    candidate_phrases.extend(ai_keywords[:5])
    candidate_phrases.extend(headings.get("h1", [])[:3])
    candidate_phrases.extend(headings.get("h2", [])[:4])

    if title:
        candidate_phrases.extend(
            part.strip()
            for part in re.split(TITLE_SEPARATOR_PATTERN, title)
            if part.strip()
        )

    if description:
        description_fragments = re.split(r"[,.|;]", description)
        candidate_phrases.extend(
            fragment.strip() for fragment in description_fragments[:3]
        )

    deduped_phrases = _dedupe_preserving_order(candidate_phrases, limit=10)
    if deduped_phrases:
        return deduped_phrases

    combined_text = " ".join(
        filter(
            None,
            [
                title,
                description,
                *headings.get("h1", []),
                *headings.get("h2", []),
            ],
        )
    )
    tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", combined_text.lower())
        if len(token) > 2 and token not in PROFILE_STOPWORDS
    ]
    common_tokens = [
        token.replace("-", " ").title()
        for token, _count in Counter(tokens).most_common(8)
    ]

    return _dedupe_preserving_order(common_tokens, limit=8)


def build_site_profile(url: str, scraped_data: dict, ai_result: dict) -> dict:
    company_name = _extract_company_name(url, scraped_data.get("title", ""))
    focus_terms = _extract_focus_terms(scraped_data, ai_result)
    core_service_pillars = focus_terms[:3] or DEFAULT_SERVICE_PILLARS
    market_focus_keywords = focus_terms[:8] or DEFAULT_MARKET_FOCUS_KEYWORDS

    business_summary = scraped_data.get("description", "").strip()
    if not business_summary:
        business_summary = scraped_data.get("title", "").strip()
    if not business_summary and market_focus_keywords:
        business_summary = (
            f"{company_name} is positioned around {market_focus_keywords[0]} and adjacent commercial search demand."
        )

    return {
        "company_name": company_name or DEFAULT_COMPANY_NAME,
        "audience_label": DEFAULT_REPORT_AUDIENCE,
        "business_summary": business_summary or DEFAULT_COMPANY_NAME,
        "core_service_pillars": core_service_pillars,
        "market_focus_keywords": market_focus_keywords,
    }
