import re
from urllib.parse import urlparse

def analyze_url_structure(url: str) -> dict:
    """
    Evaluates algorithmic URL string patterns grading mapping constraints deeply tied to core structural SEO heuristics.
    """
    score = 100
    issues = []
    recommendations = []

    parsed = urlparse(url)
    path = parsed.path
    query = parsed.query

    # 1. URL length evaluation
    if len(url) > 100:
        score -= 10
        issues.append(f"URL length exceeds optimal bounds ({len(url)} characters).")
        recommendations.append("Shorten the URL routing under 75 characters keeping paths tight to the exact commercial intent.")
    
    # 2. Query parameter boundaries
    if query or any(c in url for c in ['?', '&', '=']):
        score -= 15
        issues.append("Dynamic query parameters bounds (?, &, =) detected.")
        recommendations.append("Rewrite backend loops translating dynamic queries into static routing folders.")

    # 3. Uppercase validations
    if any(c.isupper() for c in path):
        score -= 10
        issues.append("URL contains explicit uppercase characters risking 404 case-sensitive duplication.")
        recommendations.append("Enforce strict lowercase formatting across the entire string hierarchy.")

    # 4. Hyphen and delimiter integrity
    if "_" in path:
        score -= 5
        issues.append("Underscores (_) detected preventing string fragmentation indexing.")
        recommendations.append("Replace underscores with hyphens (-) serving as strict word-separators.")
    elif "-" not in path and len(path.strip("/")) > 20:
        # Heuristic identifying unbroken massive node strings failing readability rules.
        score -= 5
        issues.append("URL contains dense, unseparated paths failing spider semantic word extractions.")
        recommendations.append("Implement descriptive word separation exclusively using hyphens.")

    # 5. Specialized ASCII violations
    special_chars = re.findall(r'[^a-zA-Z0-9\-\/\.\_]', path)
    if special_chars:
        score -= 10
        issues.append(f"Non-standard specialized characters mapped: {list(set(special_chars))}")
        recommendations.append("Sanitize the URL purging all characters except alphanumeric identifiers and hyphens.")

    # Scale score safely
    score = max(0, score)
    is_seo_friendly = score >= 70

    return {
        "url": url,
        "is_seo_friendly": is_seo_friendly,
        "issues": issues,
        "recommendations": recommendations,
        "score": score
    }
