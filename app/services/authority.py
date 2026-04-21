def calculate_page_authority(data: dict) -> int:
    """
    Simulate Page Authority (0-100) based on on-page metrics.
    Positive indicators: strong internal link count, high word count.
    Negative indicators: excessive external links.
    """
    word_count = data.get("word_count", 0)
    internal_links = data.get("internal_links_count", 0)
    if not internal_links:
        internal_links = len(data.get("internal_links", []))

    external_links = data.get("external_links_count", 0)
    if not external_links:
        external_links = len(data.get("external_links", []))

    score = 20  # Base PA

    # Content weight (up to 40 points)
    if word_count > 2000:
        score += 40
    elif word_count > 1000:
        score += 30
    elif word_count > 500:
        score += 20
    elif word_count > 200:
        score += 10

    # Internal networking weight (up to 40 points)
    if internal_links > 50:
        score += 40
    elif internal_links > 20:
        score += 30
    elif internal_links > 10:
        score += 20
    elif internal_links >= 5:
        score += 10

    # Penalize extreme outbound ratio
    if external_links > 50 and external_links > internal_links * 2:
        score -= 15
    elif external_links > 20 and external_links > internal_links:
        score -= 5

    return max(0, min(100, score))


def calculate_domain_authority(pages: list[dict]) -> int:
    """
    Simulate Domain Authority (0-100) based on aggregate site strength.
    Uses average PA of the sampled pages, boosted by total sampled scope.
    """
    if not pages:
        return 10  # Base DA

    total_pa = sum(calculate_page_authority(p) for p in pages)
    avg_pa = total_pa / len(pages)

    # Boost DA based on scale/sample size
    scale_boost = min(30, len(pages) * 2)

    da = int((avg_pa * 0.7) + scale_boost)
    return max(0, min(100, da))
