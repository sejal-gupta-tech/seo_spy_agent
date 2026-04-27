import re
from urllib.parse import urlparse


def analyze_url_structure(url: str) -> dict:
    """
    Evaluates URL SEO-friendliness against 2026 best practices.
    Checks: length, query parameters, uppercase, underscores, special characters, depth.
    """
    score = 100
    issues = []
    recommendations = []

    parsed = urlparse(url)
    path = parsed.path
    query = parsed.query

    # 1. URL total length
    if len(url) > 115:
        score -= 15
        issues.append(f"URL is too long ({len(url)} characters). Ideal is under 75.")
        recommendations.append("Shorten the URL to under 75 characters keeping only the primary keyword.")
    elif len(url) > 75:
        score -= 5
        issues.append(f"URL is slightly long ({len(url)} characters). Aim for under 75.")
        recommendations.append("Consider shortening the URL path to improve readability and click-through.")

    # 2. Query parameters (single check, not double-penalized)
    if query:
        score -= 15
        issues.append(f"URL contains dynamic query parameters: ?{query[:60]}")
        recommendations.append("Use static, keyword-rich URL paths instead of query parameters.")

    # 3. Uppercase characters in path only (not in domain)
    if any(c.isupper() for c in path):
        score -= 10
        issues.append("URL path contains uppercase characters which can cause case-sensitivity 404s.")
        recommendations.append("Enforce lowercase-only URLs across the entire site and set up redirects.")

    # 4. Underscores vs hyphens
    if "_" in path:
        score -= 5
        issues.append("URL contains underscores (_). Google treats underscores as word joiners, not separators.")
        recommendations.append("Replace all underscores with hyphens (-) for proper word separation.")
    elif len(path.strip("/")) > 20 and "-" not in path:
        score -= 5
        issues.append("URL path contains unseparated words without hyphens.")
        recommendations.append("Use hyphens to separate words in URL paths for readability and SEO.")

    # 5. Special characters (only in path, not query which is already penalized)
    special_chars = re.findall(r'[^a-zA-Z0-9\-\/\.\%]', path)
    if special_chars:
        score -= 10
        issues.append(f"URL path contains non-standard characters: {sorted(set(special_chars))}")
        recommendations.append("Remove or encode special characters from URL paths.")

    # 6. URL depth (too many folder levels)
    path_parts = [p for p in path.split("/") if p]
    if len(path_parts) > 5:
        score -= 5
        issues.append(f"URL is {len(path_parts)} levels deep. Ideal is 3 or fewer levels.")
        recommendations.append("Flatten URL structure to reduce crawl depth and improve link equity flow.")

    score = max(0, score)
    is_seo_friendly = score >= 70

    return {
        "url": url,
        "is_seo_friendly": is_seo_friendly,
        "score": score,
        "issues": issues,
        "recommendations": recommendations,
        "depth": len(path_parts),
    }
