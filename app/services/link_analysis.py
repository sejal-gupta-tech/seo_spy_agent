from app.services.authority import calculate_domain_authority

def analyze_internal_linking(pages: list) -> dict:
    """
    Evaluates internal link structure across crawled pages.
    Scores the site's internal linking density and distribution.
    """
    total_pages = len(pages)
    internal_links_count = sum(page.get("internal_links_count", 0) for page in pages)
    avg_internal_links = round(internal_links_count / total_pages, 1) if total_pages else 0

    # Identify orphan pages (pages with no incoming internal links)
    linked_urls = set()
    for page in pages:
        linked_urls.update(page.get("internal_links", []))
    page_urls = {page.get("url", "") for page in pages}
    orphan_pages = [url for url in page_urls if url not in linked_urls]

    issues = []
    recommendations = []
    score = 100

    if internal_links_count == 0:
        score = 0
        issues.append("No internal links detected across any crawled page.")
        recommendations.append("Build a hierarchical internal link structure connecting all key pages.")
    elif avg_internal_links < 3:
        score = 35
        issues.append(f"Very low average internal links per page ({avg_internal_links}).")
        recommendations.append("Each page should link to at least 3-5 related pages to distribute authority.")
    elif avg_internal_links < 8:
        score = 70
        issues.append(f"Below-average internal linking density ({avg_internal_links} links/page).")
        recommendations.append("Increase internal linking to key commercial pages and service hubs.")

    if orphan_pages:
        orphan_penalty = min(20, len(orphan_pages) * 3)
        score = max(0, score - orphan_penalty)
        issues.append(f"{len(orphan_pages)} pages receive no internal links (orphan pages).")
        recommendations.append("Add links to orphan pages from related content to improve crawlability.")

    return {
        "internal_link_score": score,
        "total_internal_links": internal_links_count,
        "avg_links_per_page": avg_internal_links,
        "orphan_page_count": len(orphan_pages),
        "orphan_pages_sample": orphan_pages[:5],
        "issues": issues,
        "recommendations": recommendations,
    }


def estimate_backlink_profile(pages: list) -> dict:
    """
    Estimates outbound link profile from crawled pages.
    NOTE: This measures outbound links (links going OUT from this site),
    NOT inbound backlinks (links coming IN from other sites).
    True backlink data requires integration with Ahrefs, Moz, or Google Search Console.
    """
    total_outbound_links = sum(page.get("external_links_count", 0) for page in pages)
    unique_domains = set()
    for page in pages:
        unique_domains.update(page.get("external_domains", []))

    outbound_domain_count = len(unique_domains)

    if outbound_domain_count < 3:
        diversity = "Low"
        diversity_note = "Very few external domains linked to. Consider adding authoritative outbound citations."
    elif outbound_domain_count < 15:
        diversity = "Medium"
        diversity_note = "Moderate outbound domain diversity. Adding more authoritative citations can improve trust signals."
    else:
        diversity = "High"
        diversity_note = "Good outbound link diversity. Ensure all external links are to reputable sources."

    da_estimate = calculate_domain_authority(pages)
    
    # Heuristic for mock backlink data based on inferred authority
    if da_estimate < 15:
        est_backlinks = da_estimate * 3 + 7
        ref_domains = max(1, int(est_backlinks / 2.5))
        strength = "Emerging"
    elif da_estimate < 40:
        est_backlinks = da_estimate * 15 + 42
        ref_domains = max(5, int(est_backlinks / 6))
        strength = "Moderate"
    elif da_estimate < 70:
        est_backlinks = da_estimate * 85 + 120
        ref_domains = max(25, int(est_backlinks / 12))
        strength = "Strong"
    else:
        est_backlinks = da_estimate * 250 + 500
        ref_domains = max(100, int(est_backlinks / 18))
        strength = "Elite"

    return {
        "backlink_strength": strength,
        "estimated_backlinks": est_backlinks,
        "referring_domains": ref_domains,
        "outbound_link_count": total_outbound_links,
        "outbound_domain_count": outbound_domain_count,
        "outbound_domain_diversity": diversity,
        "outbound_domain_note": diversity_note,
        "disclaimer": (
            "This measures outbound links and estimates inbound authority based on site signals. "
            "For precision, connect Google Search Console or a pro SEO API."
        ),
    }
