"""
Page and Domain Authority estimators.

IMPORTANT: These are heuristic estimates based on on-page signals (word count, internal/external
link counts). They are NOT equivalent to Moz Page Authority, Ahrefs Domain Rating, or any
third-party metric. They should be labelled clearly as estimated scores in any report.

True authority scores require backlink data from Google Search Console, Moz, or Ahrefs.
"""


def calculate_page_authority(data: dict) -> int:
    """
    Heuristic Page Authority estimate (0-100) based on on-page signals only.
    DO NOT present this as Moz PA or any third-party metric.
    """
    word_count = data.get("word_count", 0)
    internal_links = data.get("internal_links_count", 0) or len(data.get("internal_links", []))
    external_links = data.get("external_links_count", 0) or len(data.get("external_links", []))
    has_structured_data = data.get("has_structured_data", False)
    has_open_graph = data.get("has_open_graph", False)
    total_images = data.get("total_images", 0)

    score = 20  # Base

    # Content depth (up to 30 pts)
    if word_count > 2000:
        score += 30
    elif word_count > 1000:
        score += 22
    elif word_count > 500:
        score += 14
    elif word_count > 200:
        score += 7

    # Internal linking (up to 25 pts)
    if internal_links > 50:
        score += 25
    elif internal_links > 20:
        score += 18
    elif internal_links > 10:
        score += 12
    elif internal_links >= 3:
        score += 6

    # On-page signals (up to 15 pts)
    if has_structured_data:
        score += 6
    if has_open_graph:
        score += 4
    if total_images > 0:
        score += 5

    # Penalize spam-like outbound ratios
    if external_links > 50 and external_links > internal_links * 3:
        score -= 15
    elif external_links > 20 and external_links > internal_links * 2:
        score -= 7

    return max(0, min(100, score))


def calculate_domain_authority(pages: list[dict]) -> int:
    """
    Heuristic Domain Authority estimate (0-100) based on aggregate page signals.
    DO NOT present this as Moz DA, Ahrefs DR, or any third-party metric.
    """
    if not pages:
        return 10

    total_pa = sum(calculate_page_authority(p) for p in pages)
    avg_pa = total_pa / len(pages)

    # Scale boost: more sampled pages = more confidence in the score
    scale_boost = min(15, len(pages))

    da = int((avg_pa * 0.75) + scale_boost)
    return max(0, min(100, da))
