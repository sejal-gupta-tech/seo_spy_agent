from collections import Counter
from typing import Any, Dict

from app.core.config import (
    AUDIT_WEIGHTS,
    SEO_BENCHMARKS,
    SEO_BENCHMARK_YEAR,
    SITEWIDE_AUDIT_WEIGHTS,
    SITEWIDE_BENCHMARKS,
)
from app.utils.helpers import (
    format_percentage,
    format_ratio,
    maximum_attainment,
    minimum_attainment,
    priority_from_score,
    range_attainment,
    sort_by_priority,
    status_from_score,
    weighted_score,
)


def _snapshot(metric: str, current_value: str, benchmark: str, score: float) -> dict:
    return {
        "metric": metric,
        "current_value": current_value,
        "benchmark": benchmark,
        "status": status_from_score(score),
    }


def _count_items(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, (list, tuple, set, dict)):
        return len(value)
    if isinstance(value, bool):
        return int(value)

    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return 0


def _build_evidence(url: str, observation: str) -> list[dict]:
    if not url or not observation:
        return []
    return [{"url": url, "observation": observation}]


def _finding(
    category: str,
    metric: str,
    current_value: str,
    benchmark: str,
    score: float,
    business_impact: str,
    recommendation: str,
    priority: str,
    evidence: list[dict] | None = None,
) -> dict:
    return {
        "category": category,
        "metric": metric,
        "current_value": current_value,
        "benchmark": benchmark,
        "status": status_from_score(score),
        "business_impact": business_impact,
        "recommendation": recommendation,
        "priority": priority,
        "evidence": evidence or [],
    }


def _collect_page_evidence(
    pages: list[dict],
    predicate,
    observation_builder,
    limit: int = 3,
) -> list[dict]:
    evidence = []

    for page in pages:
        if not predicate(page):
            continue

        evidence.append(
            {
                "url": page.get("url", ""),
                "observation": observation_builder(page),
            }
        )

        if len(evidence) >= limit:
            break

    return evidence


def _build_title_finding(title: str, page_url: str = "") -> tuple[float, dict, dict]:
    benchmark = SEO_BENCHMARKS["title_length"]
    title_length = len(title)
    score = range_attainment(title_length, benchmark["min"], benchmark["max"])
    evidence = _build_evidence(page_url, f"Title length measured at {title_length} characters.")

    if not title:
        current_value = "0% benchmark attainment because the page has no title tag."
        business_impact = (
            "Missing titles reduce search-result click-through rate, weaken brand recall, "
            "and leave qualified buyers without a clear value proposition before they land."
        )
        recommendation = (
            "Publish a 50-60 character title aligned to the page's primary commercial intent."
        )
        priority = "High"
    elif benchmark["min"] <= title_length <= benchmark["max"]:
        current_value = (
            f"{format_percentage(score)} benchmark attainment with a {title_length}-character title."
        )
        business_impact = (
            "A benchmark-aligned title supports stronger click-through performance, clearer brand messaging, "
            "and steadier acquisition from high-intent searches."
        )
        recommendation = "Maintain the current title length and keep the primary keyword near the front."
        priority = "Low"
    elif title_length < benchmark["min"]:
        current_value = (
            f"{format_percentage(score)} of the minimum benchmark with a {title_length}-character title."
        )
        business_impact = (
            "Underlength titles underuse SERP real estate, lowering message clarity and reducing the probability "
            "that impressions turn into qualified visits."
        )
        recommendation = (
            "Expand the title to 50-60 characters while preserving brand and service intent."
        )
        priority = priority_from_score(score)
    else:
        current_value = (
            f"{format_percentage(score)} of the maximum benchmark with a {title_length}-character title."
        )
        business_impact = (
            "Overlength titles are more likely to truncate on mobile results pages, which weakens message control "
            "and can suppress click-through rate on revenue-driving queries."
        )
        recommendation = "Trim the title to 50-60 characters to protect mobile visibility and CTR."
        priority = priority_from_score(score)

    snapshot = _snapshot(
        metric="Title Optimization",
        current_value=current_value,
        benchmark=f"2026 standard: {benchmark['label']}.",
        score=score,
    )

    finding = _finding(
        category="Metadata",
        metric="Title Optimization",
        current_value=current_value,
        benchmark=f"2026 standard: {benchmark['label']}.",
        score=score,
        business_impact=business_impact,
        recommendation=recommendation,
        priority=priority,
        evidence=evidence,
    )

    return score, snapshot, finding


def _build_meta_description_finding(
    description: str,
    page_url: str = "",
) -> tuple[float, dict, dict]:
    benchmark = SEO_BENCHMARKS["meta_description_length"]
    description_length = len(description)
    score = range_attainment(description_length, benchmark["min"], benchmark["max"])
    evidence = _build_evidence(
        page_url,
        f"Meta description length measured at {description_length} characters.",
    )

    if not description:
        current_value = "0% benchmark attainment because no meta description was detected."
        business_impact = (
            "Missing meta descriptions leave Google to auto-generate copy, which reduces message control, "
            "weakens pre-click trust, and can dilute conversion-focused traffic."
        )
        recommendation = (
            "Add a 140-160 character meta description that communicates the page's commercial outcome."
        )
        priority = "High"
    elif benchmark["min"] <= description_length <= benchmark["max"]:
        current_value = (
            f"{format_percentage(score)} benchmark attainment with a {description_length}-character description."
        )
        business_impact = (
            "Benchmark-aligned descriptions improve SERP messaging, help qualify traffic before the click, "
            "and support stronger branded perception."
        )
        recommendation = "Maintain the current description length and refresh messaging as offers evolve."
        priority = "Low"
    elif description_length < benchmark["min"]:
        current_value = (
            f"{format_percentage(score)} of the minimum benchmark with a {description_length}-character description."
        )
        business_impact = (
            "Short descriptions often fail to communicate a full value proposition, limiting click-through rate "
            "and leaving high-intent traffic underqualified."
        )
        recommendation = (
            "Expand the description to 140-160 characters with service, outcome, and location cues."
        )
        priority = priority_from_score(score)
    else:
        current_value = (
            f"{format_percentage(score)} of the maximum benchmark with a {description_length}-character description."
        )
        business_impact = (
            "Overlength descriptions are more likely to be truncated in search, which weakens message clarity "
            "and can reduce the efficiency of organic acquisition."
        )
        recommendation = (
            "Tighten the description to 140-160 characters and keep the strongest benefit up front."
        )
        priority = priority_from_score(score)

    snapshot = _snapshot(
        metric="Meta Description",
        current_value=current_value,
        benchmark=f"2026 standard: {benchmark['label']}.",
        score=score,
    )

    finding = _finding(
        category="Metadata",
        metric="Meta Description",
        current_value=current_value,
        benchmark=f"2026 standard: {benchmark['label']}.",
        score=score,
        business_impact=business_impact,
        recommendation=recommendation,
        priority=priority,
        evidence=evidence,
    )

    return score, snapshot, finding


def _build_h1_finding(h1_tags: list[str], page_url: str = "") -> tuple[float, dict, dict]:
    benchmark = SEO_BENCHMARKS["h1_count"]
    h1_count = len(h1_tags)
    evidence = _build_evidence(page_url, f"Detected {h1_count} H1 tags on the page.")

    if h1_count == benchmark["target"]:
        score = 100.0
        current_value = "100% heading-structure compliance with a single primary H1."
        business_impact = (
            "A single H1 sharpens topical clarity for search engines and keeps the page's commercial message focused for users."
        )
        recommendation = "Maintain one authoritative H1 that reflects the primary service intent."
        priority = "Low"
    elif h1_count == 0:
        score = 0.0
        current_value = "0% heading-structure compliance because no H1 was found."
        business_impact = (
            "Without a primary H1, crawlers and users receive a weaker topical signal, which can hurt rankings, "
            "engagement, and lead-form confidence."
        )
        recommendation = "Add one clear H1 that matches the page's main service and search intent."
        priority = "High"
    else:
        score = round(100 / h1_count, 1)
        current_value = (
            f"{format_percentage(score)} alignment to the single-H1 benchmark with {h1_count} competing H1 tags."
        )
        business_impact = (
            "Multiple H1 tags split topical focus, which can confuse search engines, weaken message hierarchy, "
            "and lower conversion clarity on landing pages."
        )
        recommendation = (
            "Reduce the page to one primary H1 and move supporting statements into H2/H3 headings."
        )
        priority = "High"

    snapshot = _snapshot(
        metric="Heading Structure",
        current_value=current_value,
        benchmark=f"2026 standard: {benchmark['label']}.",
        score=score,
    )

    finding = _finding(
        category="Content Architecture",
        metric="Heading Structure",
        current_value=current_value,
        benchmark=f"2026 standard: {benchmark['label']}.",
        score=score,
        business_impact=business_impact,
        recommendation=recommendation,
        priority=priority,
        evidence=evidence,
    )

    return score, snapshot, finding


def _build_mobile_finding(
    has_viewport_meta: bool,
    page_url: str = "",
) -> tuple[float, dict, dict]:
    benchmark = SEO_BENCHMARKS["viewport_meta"]
    score = 100.0 if has_viewport_meta else 0.0
    evidence = _build_evidence(
        page_url,
        "Viewport meta tag detected." if has_viewport_meta else "Viewport meta tag missing.",
    )

    if has_viewport_meta:
        current_value = "100% mobile-first baseline compliance with a viewport declaration."
        business_impact = (
            "Viewport coverage supports mobile usability, protects engagement quality, and aligns with Google's mobile-first indexing expectations."
        )
        recommendation = (
            "Maintain the viewport declaration and validate responsive layout on revenue-driving pages."
        )
        priority = "Low"
    else:
        current_value = "0% mobile-first baseline compliance because the viewport meta tag is missing."
        business_impact = (
            "Missing viewport metadata weakens mobile usability and increases bounce risk, directly affecting lead generation and brand credibility on the dominant device class."
        )
        recommendation = (
            "Add a responsive viewport meta tag to satisfy mobile-first indexing expectations."
        )
        priority = "High"

    snapshot = _snapshot(
        metric="Mobile-First Readiness",
        current_value=current_value,
        benchmark=f"2026 standard: {benchmark['label']}.",
        score=score,
    )

    finding = _finding(
        category="Mobile Experience",
        metric="Mobile-First Readiness",
        current_value=current_value,
        benchmark=f"2026 standard: {benchmark['label']}.",
        score=score,
        business_impact=business_impact,
        recommendation=recommendation,
        priority=priority,
        evidence=evidence,
    )

    return score, snapshot, finding


def _build_image_finding(
    total_images: int,
    missing_alt: list[str],
    page_url: str = "",
) -> tuple[float, dict, dict]:
    benchmark = SEO_BENCHMARKS["alt_text_coverage"]
    optimized_images = max(total_images - len(missing_alt), 0)
    evidence = _build_evidence(
        page_url,
        f"{len(missing_alt)} of {total_images} sampled images are missing descriptive alt text.",
    )

    if total_images > 0:
        score = round((optimized_images / total_images) * 100, 1)
        current_value = (
            f"{format_ratio(optimized_images, total_images)} descriptive alt-text coverage across on-page images."
        )

        if score >= benchmark["target"]:
            business_impact = (
                "Full alt-text coverage strengthens accessibility, protects brand perception, and improves the page's ability to capture image-search visibility."
            )
            recommendation = "Maintain descriptive alt text as new visual assets are added."
            priority = "Low"
        else:
            business_impact = (
                "Incomplete alt-text coverage reduces accessibility compliance, weakens image-search discoverability, and can undermine trust with users who rely on assistive technologies."
            )
            recommendation = (
                "Add descriptive alt text to all product, service, and trust-building images."
            )
            priority = priority_from_score(score, hard_fail=score < 60)
    else:
        score = 70.0
        current_value = "0% visual-support utilization because no crawlable images were detected."
        business_impact = (
            "A page without supporting visuals misses opportunities to build trust, communicate proof points, and win incremental image-search visibility."
        )
        recommendation = "Introduce relevant visuals with descriptive alt text on key commercial pages."
        priority = "Low"

    snapshot = _snapshot(
        metric="Image Accessibility",
        current_value=current_value,
        benchmark=f"2026 standard: {benchmark['label']}.",
        score=score,
    )

    finding = _finding(
        category="Media Optimization",
        metric="Image Accessibility",
        current_value=current_value,
        benchmark=f"2026 standard: {benchmark['label']}.",
        score=score,
        business_impact=business_impact,
        recommendation=recommendation,
        priority=priority,
        evidence=evidence,
    )

    return score, snapshot, finding


def _build_link_finding(
    internal_links: int,
    external_links: int,
    page_url: str = "",
) -> tuple[float, dict, dict]:
    benchmark = SEO_BENCHMARKS["internal_link_density"]
    internal_links = _count_items(internal_links)
    external_links = _count_items(external_links)
    total_links = internal_links + external_links
    density = round((internal_links / total_links) * 100, 1) if total_links else 0.0
    evidence = _build_evidence(
        page_url,
        f"Internal link density measured at {format_percentage(density)} from {total_links} crawlable links.",
    )

    if total_links == 0:
        score = 0.0
        current_value = "0% internal link density because the page exposes no crawlable links."
        business_impact = (
            "Pages without crawlable links trap authority, limit discovery of adjacent revenue pages, and reduce the site's ability to guide visitors into conversion paths."
        )
        recommendation = (
            "Add internal links to related services, proof pages, and conversion destinations."
        )
        priority = "High"
    else:
        score = (
            100.0
            if density >= benchmark["min"]
            else round((density / benchmark["min"]) * 100, 1)
        )
        current_value = f"{format_percentage(density)} internal link density across crawlable links."

        if density >= benchmark["min"]:
            business_impact = (
                "Healthy internal linking improves crawl efficiency, distributes authority to commercial pages, and helps visitors move deeper into lead-generation funnels."
            )
            recommendation = (
                "Maintain strong internal pathways from this page into adjacent service and contact pages."
            )
            priority = "Low"
        else:
            business_impact = (
                "Low internal link density slows crawler discovery and weakens the handoff from informational pages into high-intent conversion journeys."
            )
            recommendation = (
                "Increase internal links to related service, case-study, and contact pages to strengthen crawl flow and conversions."
            )
            priority = priority_from_score(score, hard_fail=density < 35)

    snapshot = _snapshot(
        metric="Internal Link Density",
        current_value=current_value,
        benchmark=f"2026 standard: {benchmark['label']}.",
        score=score,
    )

    finding = _finding(
        category="Internal Linking",
        metric="Internal Link Density",
        current_value=current_value,
        benchmark=f"2026 standard: {benchmark['label']}.",
        score=score,
        business_impact=business_impact,
        recommendation=recommendation,
        priority=priority,
        evidence=evidence,
    )

    return score, snapshot, finding


def audit_seo(data: Dict[str, Any], page_url: str = "") -> dict:
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    h1_tags = data.get("headings", {}).get("h1", [])
    total_images = data.get("total_images", 0)
    missing_alt = data.get("missing_alt_images", [])
    internal_links = _count_items(data.get("internal_links"))
    if not internal_links:
        internal_links = _count_items(data.get("internal_links_count", 0))

    external_links = _count_items(data.get("external_links"))
    if not external_links:
        external_links = _count_items(data.get("external_links_count", 0))
    has_viewport_meta = bool(data.get("has_viewport_meta"))

    scores = {}
    metric_summary = []
    findings = []

    title_score, title_snapshot, title_finding = _build_title_finding(title, page_url)
    scores["title"] = title_score
    metric_summary.append(title_snapshot)
    findings.append(title_finding)

    meta_score, meta_snapshot, meta_finding = _build_meta_description_finding(
        description,
        page_url,
    )
    scores["meta_description"] = meta_score
    metric_summary.append(meta_snapshot)
    findings.append(meta_finding)

    heading_score, heading_snapshot, heading_finding = _build_h1_finding(h1_tags, page_url)
    scores["heading_structure"] = heading_score
    metric_summary.append(heading_snapshot)
    findings.append(heading_finding)

    mobile_score, mobile_snapshot, mobile_finding = _build_mobile_finding(
        has_viewport_meta,
        page_url,
    )
    scores["mobile_first"] = mobile_score
    metric_summary.append(mobile_snapshot)
    findings.append(mobile_finding)

    image_score, image_snapshot, image_finding = _build_image_finding(
        total_images,
        missing_alt,
        page_url,
    )
    scores["image_accessibility"] = image_score
    metric_summary.append(image_snapshot)
    findings.append(image_finding)

    link_score, link_snapshot, link_finding = _build_link_finding(
        internal_links,
        external_links,
        page_url,
    )
    scores["linking_strategy"] = link_score
    metric_summary.append(link_snapshot)
    findings.append(link_finding)

    overall_score = weighted_score(scores, AUDIT_WEIGHTS)
    metadata_score = round((title_score + meta_score) / 2, 1)

    return {
        "benchmark_reference_year": SEO_BENCHMARK_YEAR,
        "overall_score": overall_score,
        "overall_seo_health": format_percentage(overall_score),
        "metric_summary": metric_summary,
        "findings": sort_by_priority(findings),
        "category_scores": {
            "metadata": format_percentage(metadata_score),
            "content_structure": format_percentage(heading_score),
            "mobile_first": format_percentage(mobile_score),
            "image_accessibility": format_percentage(image_score),
            "internal_link_density": format_percentage(link_score),
        },
    }


def _percentage_count(matched: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((matched / total) * 100, 1)


def _sitewide_coverage_finding(
    metric_key: str,
    metric_name: str,
    matched_count: int,
    total_count: int,
    category: str,
    business_impact: str,
    recommendation: str,
    evidence: list[dict],
) -> tuple[float, dict, dict]:
    benchmark = SITEWIDE_BENCHMARKS[metric_key]
    percentage = _percentage_count(matched_count, total_count)
    score = minimum_attainment(percentage, benchmark["min"])
    current_value = (
        f"{format_percentage(percentage)} of sampled pages ({matched_count}/{total_count}) meet this benchmark."
    )
    priority = priority_from_score(score, hard_fail=percentage < benchmark["min"] * 0.6)

    snapshot = _snapshot(
        metric=metric_name,
        current_value=current_value,
        benchmark=f"2026 standard: {benchmark['label']}.",
        score=score,
    )

    finding = _finding(
        category=category,
        metric=metric_name,
        current_value=current_value,
        benchmark=f"2026 standard: {benchmark['label']}.",
        score=score,
        business_impact=business_impact,
        recommendation=recommendation,
        priority=priority,
        evidence=evidence,
    )

    return score, snapshot, finding


def _build_page_summary(page: dict, page_audit: dict) -> dict:
    findings = page_audit.get("findings", [])
    top_issue = "No major sampled issue"

    if findings:
        top_finding = findings[0]
        top_issue = f"{top_finding['metric']}: {top_finding['status']}"

    return {
        "url": page.get("url", ""),
        "page_type": page.get("page_type", "Other"),
        "title": page.get("title") or page.get("url", ""),
        "word_count": page.get("word_count", 0),
        "seo_health": page_audit.get("overall_seo_health", "0%"),
        "key_issue": top_issue,
    }


def _duplicate_coverage(pages: list[dict], field_name: str) -> tuple[int, list[dict]]:
    values = [page.get(field_name, "").strip() for page in pages if page.get(field_name, "").strip()]
    counter = Counter(values)
    duplicate_values = {value for value, count in counter.items() if count > 1}
    duplicate_pages = [page for page in pages if page.get(field_name, "").strip() in duplicate_values]
    unique_count = len([page for page in pages if page.get(field_name, "").strip() not in duplicate_values and page.get(field_name, "").strip()])
    return unique_count, duplicate_pages


def audit_sitewide(crawl_data: Dict[str, Any], page_audits: list[dict]) -> dict:
    pages = crawl_data.get("pages", [])
    total_pages = len(pages)

    if total_pages == 0:
        return {
            "benchmark_reference_year": SEO_BENCHMARK_YEAR,
            "overall_score": 0.0,
            "overall_seo_health": "0%",
            "metric_summary": [],
            "findings": [],
            "page_summaries": [],
            "category_scores": {},
        }

    findings = []
    metric_summary = []
    score_map = {}

    title_optimized_pages = [
        page
        for page in pages
        if SEO_BENCHMARKS["title_length"]["min"]
        <= page.get("title_length", 0)
        <= SEO_BENCHMARKS["title_length"]["max"]
    ]
    score, snapshot, finding = _sitewide_coverage_finding(
        metric_key="title_coverage",
        metric_name="Title Coverage",
        matched_count=len(title_optimized_pages),
        total_count=total_pages,
        category="Metadata",
        business_impact=(
            "Low title coverage weakens search-result messaging across the site, reducing click-through rate and making demand capture inconsistent."
        ),
        recommendation=(
            "Normalize titles across sampled pages so each one lands within the benchmark range and reflects unique search intent."
        ),
        evidence=_collect_page_evidence(
            pages,
            lambda page: not (
                SEO_BENCHMARKS["title_length"]["min"]
                <= page.get("title_length", 0)
                <= SEO_BENCHMARKS["title_length"]["max"]
            ),
            lambda page: f"Title length is {page.get('title_length', 0)} characters.",
        ),
    )
    score_map["title_coverage"] = score
    metric_summary.append(snapshot)
    findings.append(finding)

    meta_optimized_pages = [
        page
        for page in pages
        if SEO_BENCHMARKS["meta_description_length"]["min"]
        <= page.get("meta_description_length", 0)
        <= SEO_BENCHMARKS["meta_description_length"]["max"]
    ]
    score, snapshot, finding = _sitewide_coverage_finding(
        metric_key="meta_description_coverage",
        metric_name="Meta Description Coverage",
        matched_count=len(meta_optimized_pages),
        total_count=total_pages,
        category="Metadata",
        business_impact=(
            "Weak description coverage reduces message control in search snippets and leaves too much conversion-critical copy to Google's automation."
        ),
        recommendation=(
            "Write unique 140-160 character descriptions for every commercially relevant sampled page."
        ),
        evidence=_collect_page_evidence(
            pages,
            lambda page: not (
                SEO_BENCHMARKS["meta_description_length"]["min"]
                <= page.get("meta_description_length", 0)
                <= SEO_BENCHMARKS["meta_description_length"]["max"]
            ),
            lambda page: (
                f"Meta description length is {page.get('meta_description_length', 0)} characters."
            ),
        ),
    )
    score_map["meta_description_coverage"] = score
    metric_summary.append(snapshot)
    findings.append(finding)

    h1_compliant_pages = [page for page in pages if page.get("h1_count", 0) == 1]
    score, snapshot, finding = _sitewide_coverage_finding(
        metric_key="h1_compliance",
        metric_name="H1 Compliance",
        matched_count=len(h1_compliant_pages),
        total_count=total_pages,
        category="Content Architecture",
        business_impact=(
            "Inconsistent H1 usage creates weak topical hierarchy across the site and makes it harder for both crawlers and buyers to understand page purpose quickly."
        ),
        recommendation=(
            "Standardize each sampled page to one clear H1 tied to the page's primary intent."
        ),
        evidence=_collect_page_evidence(
            pages,
            lambda page: page.get("h1_count", 0) != 1,
            lambda page: f"Detected {page.get('h1_count', 0)} H1 tags.",
        ),
    )
    score_map["h1_compliance"] = score
    metric_summary.append(snapshot)
    findings.append(finding)

    canonical_pages = [page for page in pages if page.get("has_canonical")]
    score, snapshot, finding = _sitewide_coverage_finding(
        metric_key="canonical_coverage",
        metric_name="Canonical Coverage",
        matched_count=len(canonical_pages),
        total_count=total_pages,
        category="Indexation Governance",
        business_impact=(
            "Weak canonical coverage increases the probability of duplicate content confusion, diluted ranking signals, and unstable indexing outcomes."
        ),
        recommendation=(
            "Add self-referencing canonical tags to sampled indexable pages and verify they resolve cleanly."
        ),
        evidence=_collect_page_evidence(
            pages,
            lambda page: not page.get("has_canonical"),
            lambda _page: "Canonical tag missing.",
        ),
    )
    score_map["canonical_coverage"] = score
    metric_summary.append(snapshot)
    findings.append(finding)

    indexable_pages = [page for page in pages if page.get("is_indexable", True)]
    score, snapshot, finding = _sitewide_coverage_finding(
        metric_key="indexability_coverage",
        metric_name="Indexability Coverage",
        matched_count=len(indexable_pages),
        total_count=total_pages,
        category="Indexation Governance",
        business_impact=(
            "Unexpected noindex directives suppress organic reach and can remove strategic pages from the revenue pipeline."
        ),
        recommendation=(
            "Review every sampled noindex page and confirm it is intentionally excluded from search."
        ),
        evidence=_collect_page_evidence(
            pages,
            lambda page: not page.get("is_indexable", True),
            lambda page: (
                f"Page marked non-indexable via robots directives: {page.get('robots_directives', 'noindex')}."
            ),
        ),
    )
    score_map["indexability_coverage"] = score
    metric_summary.append(snapshot)
    findings.append(finding)

    structured_data_pages = [page for page in pages if page.get("has_structured_data")]
    score, snapshot, finding = _sitewide_coverage_finding(
        metric_key="structured_data_coverage",
        metric_name="Structured Data Adoption",
        matched_count=len(structured_data_pages),
        total_count=total_pages,
        category="SERP Enhancements",
        business_impact=(
            "Low schema adoption limits eligibility for richer SERP treatments and can weaken search engines' understanding of the site's entities and offers."
        ),
        recommendation=(
            "Implement structured data on the homepage and core commercial pages, starting with Organization, Website, Service, and Breadcrumb schema where appropriate."
        ),
        evidence=_collect_page_evidence(
            pages,
            lambda page: not page.get("has_structured_data"),
            lambda _page: "No structured data detected.",
        ),
    )
    score_map["structured_data_coverage"] = score
    metric_summary.append(snapshot)
    findings.append(finding)

    social_metadata_pages = [
        page
        for page in pages
        if page.get("has_open_graph") or page.get("has_twitter_card")
    ]
    score, snapshot, finding = _sitewide_coverage_finding(
        metric_key="social_metadata_coverage",
        metric_name="Social Metadata Coverage",
        matched_count=len(social_metadata_pages),
        total_count=total_pages,
        category="Brand Distribution",
        business_impact=(
            "Weak Open Graph and Twitter coverage reduces control over how the brand appears when pages are shared, which affects click-through and perceived credibility."
        ),
        recommendation=(
            "Add consistent Open Graph and Twitter metadata to all sampled marketing and trust-building pages."
        ),
        evidence=_collect_page_evidence(
            pages,
            lambda page: not (
                page.get("has_open_graph") or page.get("has_twitter_card")
            ),
            lambda _page: "No Open Graph or Twitter card metadata detected.",
        ),
    )
    score_map["social_metadata_coverage"] = score
    metric_summary.append(snapshot)
    findings.append(finding)

    substantive_pages = [page for page in pages if page.get("word_count", 0) >= 300]
    score, snapshot, finding = _sitewide_coverage_finding(
        metric_key="substantive_content_coverage",
        metric_name="Substantive Content Coverage",
        matched_count=len(substantive_pages),
        total_count=total_pages,
        category="Content Depth",
        business_impact=(
            "Thin commercial pages struggle to answer buyer questions, making it harder to rank competitively and convert interest into enquiries."
        ),
        recommendation=(
            "Expand sampled thin pages with clearer service detail, proof points, FAQs, and conversion cues."
        ),
        evidence=_collect_page_evidence(
            pages,
            lambda page: page.get("word_count", 0) < 300,
            lambda page: f"Word count measured at {page.get('word_count', 0)} words.",
        ),
    )
    score_map["substantive_content_coverage"] = score
    metric_summary.append(snapshot)
    findings.append(finding)

    total_images = sum(page.get("total_images", 0) for page in pages)
    optimized_images = sum(
        max(page.get("total_images", 0) - len(page.get("missing_alt_images", [])), 0)
        for page in pages
    )
    alt_text_percentage = (
        round((optimized_images / total_images) * 100, 1) if total_images else 75.0
    )
    alt_score = minimum_attainment(
        alt_text_percentage,
        SITEWIDE_BENCHMARKS["alt_text_coverage"]["min"],
    )
    alt_current_value = (
        f"{format_percentage(alt_text_percentage)} sitewide alt-text coverage across sampled images."
        if total_images
        else "No sampled images detected across crawled pages."
    )
    alt_finding = _finding(
        category="Media Optimization",
        metric="Sitewide Alt Text Coverage",
        current_value=alt_current_value,
        benchmark=f"2026 standard: {SITEWIDE_BENCHMARKS['alt_text_coverage']['label']}.",
        score=alt_score,
        business_impact=(
            "Poor alt-text discipline weakens accessibility coverage, limits image search visibility, and chips away at trust on visually important pages."
        ),
        recommendation=(
            "Audit image libraries and enforce descriptive alt text on all functional and trust-building images."
        ),
        priority=priority_from_score(alt_score, hard_fail=alt_text_percentage < 60),
        evidence=_collect_page_evidence(
            pages,
            lambda page: len(page.get("missing_alt_images", [])) > 0,
            lambda page: (
                f"{len(page.get('missing_alt_images', []))} images missing alt text out of {page.get('total_images', 0)}."
            ),
        ),
    )
    score_map["alt_text_coverage"] = alt_score
    metric_summary.append(
        _snapshot(
            metric="Sitewide Alt Text Coverage",
            current_value=alt_current_value,
            benchmark=f"2026 standard: {SITEWIDE_BENCHMARKS['alt_text_coverage']['label']}.",
            score=alt_score,
        )
    )
    findings.append(alt_finding)

    broken_link_summary = crawl_data.get("broken_link_summary", {})
    broken_ratio = float(broken_link_summary.get("broken_ratio", 0.0))
    broken_score = maximum_attainment(
        broken_ratio,
        SITEWIDE_BENCHMARKS["broken_internal_link_ratio"]["max"],
    )
    broken_current_value = (
        f"{format_percentage(broken_ratio)} broken internal links across checked samples "
        f"({broken_link_summary.get('broken_count', 0)}/{broken_link_summary.get('checked_count', 0)})."
    )
    broken_finding = _finding(
        category="Link Integrity",
        metric="Broken Internal Link Ratio",
        current_value=broken_current_value,
        benchmark=f"2026 standard: {SITEWIDE_BENCHMARKS['broken_internal_link_ratio']['label']}.",
        score=broken_score,
        business_impact=(
            "Broken internal links interrupt journeys to key pages, waste crawl budget, and signal weak operational hygiene to both users and search engines."
        ),
        recommendation=(
            "Repair or redirect broken internal targets found in the sampled crawl and add QA checks before publishing."
        ),
        priority=priority_from_score(broken_score, hard_fail=broken_ratio > 5),
        evidence=[
            {
                "url": item.get("source_url", ""),
                "observation": (
                    f"Links to {item.get('target_url', '')} returned status {item.get('status_code', 0)}."
                ),
            }
            for item in broken_link_summary.get("broken_links", [])[:3]
        ],
    )
    score_map["broken_internal_link_ratio"] = broken_score
    metric_summary.append(
        _snapshot(
            metric="Broken Internal Link Ratio",
            current_value=broken_current_value,
            benchmark=f"2026 standard: {SITEWIDE_BENCHMARKS['broken_internal_link_ratio']['label']}.",
            score=broken_score,
        )
    )
    findings.append(broken_finding)

    unique_title_count, duplicate_title_pages = _duplicate_coverage(pages, "title")
    unique_title_percentage = _percentage_count(unique_title_count, total_pages)
    unique_title_score = minimum_attainment(
        unique_title_percentage,
        SITEWIDE_BENCHMARKS["unique_title_coverage"]["min"],
    )
    unique_title_current_value = (
        f"{format_percentage(unique_title_percentage)} unique titles across sampled pages."
    )
    unique_title_finding = _finding(
        category="Metadata",
        metric="Title Uniqueness",
        current_value=unique_title_current_value,
        benchmark=f"2026 standard: {SITEWIDE_BENCHMARKS['unique_title_coverage']['label']}.",
        score=unique_title_score,
        business_impact=(
            "Duplicate titles make pages compete for the same query meaning and reduce the site's ability to match distinct search intents with distinct landing experiences."
        ),
        recommendation=(
            "Rewrite duplicate titles so each sampled page owns a distinct topic and click-through proposition."
        ),
        priority=priority_from_score(unique_title_score, hard_fail=unique_title_percentage < 80),
        evidence=_collect_page_evidence(
            duplicate_title_pages,
            lambda _page: True,
            lambda page: f"Duplicate title detected: {page.get('title', '')}.",
        ),
    )
    score_map["unique_title_coverage"] = unique_title_score
    metric_summary.append(
        _snapshot(
            metric="Title Uniqueness",
            current_value=unique_title_current_value,
            benchmark=f"2026 standard: {SITEWIDE_BENCHMARKS['unique_title_coverage']['label']}.",
            score=unique_title_score,
        )
    )
    findings.append(unique_title_finding)

    unique_meta_count, duplicate_meta_pages = _duplicate_coverage(pages, "description")
    unique_meta_percentage = _percentage_count(unique_meta_count, total_pages)
    unique_meta_score = minimum_attainment(
        unique_meta_percentage,
        SITEWIDE_BENCHMARKS["unique_meta_coverage"]["min"],
    )
    unique_meta_current_value = (
        f"{format_percentage(unique_meta_percentage)} unique meta descriptions across sampled pages."
    )
    unique_meta_finding = _finding(
        category="Metadata",
        metric="Meta Description Uniqueness",
        current_value=unique_meta_current_value,
        benchmark=f"2026 standard: {SITEWIDE_BENCHMARKS['unique_meta_coverage']['label']}.",
        score=unique_meta_score,
        business_impact=(
            "Duplicate descriptions weaken differentiation between pages and reduce the chance of matching pre-click messaging to the user's exact need."
        ),
        recommendation=(
            "Replace duplicate descriptions with intent-specific copy for each sampled page."
        ),
        priority=priority_from_score(unique_meta_score, hard_fail=unique_meta_percentage < 80),
        evidence=_collect_page_evidence(
            duplicate_meta_pages,
            lambda _page: True,
            lambda page: (
                f"Duplicate description detected at {page.get('meta_description_length', 0)} characters."
            ),
        ),
    )
    score_map["unique_meta_coverage"] = unique_meta_score
    metric_summary.append(
        _snapshot(
            metric="Meta Description Uniqueness",
            current_value=unique_meta_current_value,
            benchmark=f"2026 standard: {SITEWIDE_BENCHMARKS['unique_meta_coverage']['label']}.",
            score=unique_meta_score,
        )
    )
    findings.append(unique_meta_finding)

    robots_exists = bool(crawl_data.get("robots", {}).get("exists"))
    robots_score = 100.0 if robots_exists else 0.0
    findings.append(
        _finding(
            category="Crawl Governance",
            metric="Robots.txt Presence",
            current_value="Robots.txt found." if robots_exists else "Robots.txt not found.",
            benchmark="2026 standard: Robots.txt should be accessible and actively maintained.",
            score=robots_score,
            business_impact=(
                "Missing robots.txt removes a simple layer of crawl governance and can make large-site control more fragile as the site grows."
            ),
            recommendation=(
                "Publish and maintain a robots.txt file with clear crawler directives and sitemap references."
            ),
            priority="Low" if robots_exists else "Medium",
            evidence=_build_evidence(
                crawl_data.get("robots", {}).get("url", ""),
                f"Robots.txt returned status {crawl_data.get('robots', {}).get('status_code', 0)}.",
            ),
        )
    )

    sitemap_exists = bool(crawl_data.get("sitemap", {}).get("exists")) or bool(
        crawl_data.get("declared_sitemaps", [])
    )
    sitemap_score = 100.0 if sitemap_exists else 0.0
    findings.append(
        _finding(
            category="Crawl Governance",
            metric="XML Sitemap Presence",
            current_value="Sitemap discovered." if sitemap_exists else "No sitemap discovered.",
            benchmark="2026 standard: XML sitemap available and referenced for indexable pages.",
            score=sitemap_score,
            business_impact=(
                "Without a visible sitemap, search engines can take longer to discover new or updated commercial pages, slowing indexation and visibility gains."
            ),
            recommendation=(
                "Publish an XML sitemap and reference it in robots.txt so discovery stays efficient as the site expands."
            ),
            priority="Low" if sitemap_exists else "Medium",
            evidence=_build_evidence(
                crawl_data.get("sitemap", {}).get("url", ""),
                f"Sitemap endpoint returned status {crawl_data.get('sitemap', {}).get('status_code', 0)}.",
            ),
        )
    )

    overall_score = weighted_score(score_map, SITEWIDE_AUDIT_WEIGHTS)

    page_summaries = [
        _build_page_summary(page, page_audit)
        for page, page_audit in zip(pages, page_audits, strict=False)
    ]

    return {
        "benchmark_reference_year": SEO_BENCHMARK_YEAR,
        "overall_score": overall_score,
        "overall_seo_health": format_percentage(overall_score),
        "metric_summary": metric_summary,
        "findings": sort_by_priority(findings),
        "page_summaries": page_summaries,
        "category_scores": {
            "metadata": format_percentage(
                weighted_score(
                    {
                        "title_coverage": score_map["title_coverage"],
                        "meta_description_coverage": score_map["meta_description_coverage"],
                        "unique_title_coverage": score_map["unique_title_coverage"],
                        "unique_meta_coverage": score_map["unique_meta_coverage"],
                    },
                    {
                        "title_coverage": 4,
                        "meta_description_coverage": 4,
                        "unique_title_coverage": 1,
                        "unique_meta_coverage": 1,
                    },
                )
            ),
            "content_depth": format_percentage(score_map["substantive_content_coverage"]),
            "indexation_governance": format_percentage(
                weighted_score(
                    {
                        "canonical_coverage": score_map["canonical_coverage"],
                        "indexability_coverage": score_map["indexability_coverage"],
                    },
                    {
                        "canonical_coverage": 1,
                        "indexability_coverage": 1,
                    },
                )
            ),
            "serp_enhancements": format_percentage(
                weighted_score(
                    {
                        "structured_data_coverage": score_map["structured_data_coverage"],
                        "social_metadata_coverage": score_map["social_metadata_coverage"],
                    },
                    {
                        "structured_data_coverage": 1,
                        "social_metadata_coverage": 1,
                    },
                )
            ),
        },
    }
