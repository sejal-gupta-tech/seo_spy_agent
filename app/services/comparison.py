import json
import re

import httpx
from bs4 import BeautifulSoup

from app.core.logger import logger
from app.core.config import (
    COMPETITOR_FETCH_TIMEOUT_SECONDS,
    DEFAULT_COMPANY_NAME,
    DEFAULT_MARKET_FOCUS_KEYWORDS,
    DEFAULT_SERVICE_PILLARS,
)
from app.utils.helpers import format_percentage
from app.core.openai_client import get_openai_client

STOPWORDS = {
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
}


async def get_page_headings(url: str) -> list[str]:
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        async with httpx.AsyncClient(timeout=COMPETITOR_FETCH_TIMEOUT_SECONDS) as client_http:
            response = await client_http.get(
                url,
                headers=headers,
                follow_redirects=True,
            )
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        headings = []
        for tag in ["h1", "h2", "h3"]:
            headings.extend(h.get_text(strip=True) for h in soup.find_all(tag))

        return headings

    except Exception:
        return []


def _tokenize_headings(headings: list[str]) -> set[str]:
    tokens = set()

    for heading in headings:
        words = re.findall(r"[a-z0-9]+", heading.lower())
        filtered_words = [word for word in words if len(word) > 2 and word not in STOPWORDS]
        tokens.update(filtered_words)

    return tokens


def _calculate_overlap(user_headings: list[str], competitor_headings: list[str]) -> tuple[float, float]:
    user_terms = _tokenize_headings(user_headings)
    competitor_terms = _tokenize_headings(competitor_headings)

    if not competitor_terms:
        return 0.0, 100.0

    overlap_terms = user_terms & competitor_terms
    overlap_score = round((len(overlap_terms) / len(competitor_terms)) * 100, 1)
    content_gap = round(max(100.0 - overlap_score, 0.0), 1)

    return overlap_score, content_gap


def _normalize_priority(priority: str, score: int) -> str:
    if priority in {"High", "Medium", "Low"}:
        return priority
    if score >= 8:
        return "High"
    if score >= 5:
        return "Medium"
    return "Low"


def _priority_rank(priority: str) -> int:
    return {"High": 0, "Medium": 1, "Low": 2}.get(priority, 9)


def _dedupe_terms(values: list[str], limit: int) -> list[str]:
    seen = set()
    deduped = []

    for value in values:
        cleaned_value = " ".join(str(value).split()).strip()
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


def _fallback_market_opportunities(
    content_gap_ratio: str,
    seed_keyword: str,
    site_profile: dict,
) -> list[dict]:
    company_name = site_profile.get("company_name") or DEFAULT_COMPANY_NAME
    service_pillars = site_profile.get("core_service_pillars") or DEFAULT_SERVICE_PILLARS
    market_focus_keywords = site_profile.get("market_focus_keywords") or DEFAULT_MARKET_FOCUS_KEYWORDS

    candidate_keywords = _dedupe_terms(
        [seed_keyword, *market_focus_keywords, *service_pillars],
        limit=5,
    )

    if not candidate_keywords:
        candidate_keywords = DEFAULT_MARKET_FOCUS_KEYWORDS

    opportunities = []

    for index, keyword in enumerate(candidate_keywords, start=1):
        score = max(10 - index + 1, 6)
        opportunities.append(
            {
                "keyword": keyword,
                "market_opportunity_score": score,
                "relevance_to_business": (
                    f"High alignment with {company_name}'s visible service themes and commercial positioning."
                ),
                "supporting_gap_ratio": content_gap_ratio,
                "business_impact": (
                    f"Closing this gap can expand {company_name}'s qualified organic reach and improve conversion-ready search visibility."
                ),
                "recommendation": "Create or strengthen dedicated content sections that target this commercial topic.",
                "priority": _normalize_priority("", score),
            }
        )

    return opportunities


def _sanitize_market_opportunities(
    opportunities: list[dict],
    content_gap_ratio: str,
    site_profile: dict,
) -> list[dict]:
    company_name = site_profile.get("company_name") or DEFAULT_COMPANY_NAME
    sanitized = []

    for item in opportunities:
        raw_score = item.get("market_opportunity_score", 0)

        try:
            score = int(raw_score)
        except (TypeError, ValueError):
            score = 0

        score = max(1, min(score, 10))
        priority = _normalize_priority(item.get("priority", ""), score)

        sanitized.append(
            {
                "keyword": str(item.get("keyword", "")).strip(),
                "market_opportunity_score": score,
                "relevance_to_business": str(
                    item.get(
                        "relevance_to_business",
                        f"Aligned to {company_name}'s visible service mix.",
                    )
                ).strip(),
                "supporting_gap_ratio": str(
                    item.get("supporting_gap_ratio", content_gap_ratio)
                ).strip()
                or content_gap_ratio,
                "business_impact": str(
                    item.get(
                        "business_impact",
                        f"Improving coverage here can unlock more qualified demand for {company_name}.",
                    )
                ).strip(),
                "recommendation": str(
                    item.get(
                        "recommendation",
                        "Expand page coverage around this topic with clearer commercial intent.",
                    )
                ).strip(),
                "priority": priority,
            }
        )

    sanitized = [item for item in sanitized if item["keyword"]]
    sanitized.sort(
        key=lambda item: (-item["market_opportunity_score"], _priority_rank(item["priority"]))
    )

    return sanitized[:5]


def _generate_market_opportunities(
    user_headings: list[str],
    competitor_headings: list[str],
    content_gap_ratio: str,
    seed_keyword: str,
    site_profile: dict,
) -> list[dict]:
    client = get_openai_client()
    company_name = site_profile.get("company_name") or DEFAULT_COMPANY_NAME
    business_summary = site_profile.get("business_summary") or company_name
    core_service_pillars = site_profile.get("core_service_pillars") or DEFAULT_SERVICE_PILLARS
    market_focus_keywords = site_profile.get("market_focus_keywords") or DEFAULT_MARKET_FOCUS_KEYWORDS

    prompt = f"""
    You are an Elite SEO Strategist preparing a board-facing market opportunity report.

    Website brand:
    {company_name}

    Website business summary:
    {business_summary}

    Core service pillars inferred from the page:
    {core_service_pillars}

    Market focus keywords inferred from the page:
    {market_focus_keywords}

    User page headings:
    {user_headings}

    Competitor headings:
    {competitor_headings}

    Seed keyword:
    {seed_keyword or market_focus_keywords[0]}

    Task:
    1. Identify up to 5 missing market opportunities for this specific website.
    2. Rank each one with a market_opportunity_score from 1 to 10 based on relevance to this site's visible services and commercial intent.
    3. Keep recommendations short, strategic, and ROI focused.

    Return JSON only using this format:
    {{
      "market_opportunities": [
        {{
          "keyword": "example keyword",
          "market_opportunity_score": 8,
          "relevance_to_business": "Direct fit to the website's commercial offer.",
          "supporting_gap_ratio": "{content_gap_ratio}",
          "business_impact": "Stronger visibility here can increase qualified organic pipeline.",
          "recommendation": "Create or expand a dedicated section targeting this topic.",
          "priority": "High"
        }}
      ]
    }}
    """

    if not client:
        return _fallback_market_opportunities(content_gap_ratio, seed_keyword, site_profile)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict SEO strategist that returns valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)
        opportunities = parsed.get("market_opportunities", [])

        if not isinstance(opportunities, list):
            raise ValueError("Invalid market opportunities format")

        return _sanitize_market_opportunities(opportunities, content_gap_ratio, site_profile)

    except Exception:
        logger.exception("Failed to generate market opportunities with AI.")
        return _fallback_market_opportunities(content_gap_ratio, seed_keyword, site_profile)


def compare_with_competitors(
    user_headings: list[str],
    competitor_headings: list[str],
    seed_keyword: str = "",
    site_profile: dict | None = None,
) -> dict:
    site_profile = site_profile or {}
    overlap_score, content_gap = _calculate_overlap(user_headings, competitor_headings)
    keyword_overlap_score = format_percentage(overlap_score)
    content_gap_ratio = format_percentage(content_gap)

    market_opportunities = _generate_market_opportunities(
        user_headings=user_headings,
        competitor_headings=competitor_headings,
        content_gap_ratio=content_gap_ratio,
        seed_keyword=seed_keyword,
        site_profile=site_profile,
    )

    market_opportunities.sort(
        key=lambda item: (-item["market_opportunity_score"], _priority_rank(item["priority"]))
    )

    return {
        "keyword_overlap_score": keyword_overlap_score,
        "content_gap_ratio": content_gap_ratio,
        "market_opportunities": market_opportunities,
    }
