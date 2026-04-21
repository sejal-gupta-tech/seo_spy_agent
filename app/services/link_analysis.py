def analyze_internal_linking(pages: list) -> dict:
    """
    Evaluates the localized internal link spread across crawled pages mapping site hierarchy density.
    """
    internal_links_count = sum(page.get("internal_links_count", 0) for page in pages)
    issues = []
    recommendations = []
    score = 100

    if internal_links_count == 0:
        score = 0
        issues.append("Critical: No internal links detected across sampled pages.")
        recommendations.append("Immediately construct a hierarchical site architecture routing traffic to key structural pages.")
    elif internal_links_count < 5:
        score = 40
        issues.append("Weak internal linking structure detected. Low crawlability mapped.")
        recommendations.append("Add internal links to improve crawlability and distribute page authority securely.")
    elif internal_links_count < 15:
        score = 75
        issues.append("Internal referencing density is slightly constrained.")
        recommendations.append("Map clustered content pathways to boost user time-on-site.")

    return {
        "internal_link_score": score,
        "issues": issues,
        "recommendations": recommendations,
    }

def estimate_backlink_profile(pages: list) -> dict:
    """
    Simulates external entity references weighting simulated trust proxies locally.
    """
    external_links_count = sum(page.get("external_links_count", 0) for page in pages)
    unique_domains = set()
    for page in pages:
        unique_domains.update(page.get("external_domains", []))
    
    referring_domains = len(unique_domains)
    estimated_backlinks = min(external_links_count * 2, 500)  # Simulated proxy expansion
    
    if external_links_count < 5:
        strength = "Low"
    elif external_links_count < 20:
        strength = "Medium"
    else:
        strength = "High"

    return {
        "backlink_strength": strength,
        "estimated_backlinks": estimated_backlinks,
        "referring_domains": referring_domains,
    }
