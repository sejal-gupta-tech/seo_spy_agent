import asyncio

from app.core.logger import logger
from app.services.ai_seo import extract_main_keyword, generate_seo_suggestions
from app.services.audit import audit_seo, audit_sitewide
from app.services.comparison import compare_with_competitors, get_page_headings
from app.services.competitor import get_top_competitors
from app.services.crawler import crawl_site
from app.services.report_builder import (
    build_data_limitations,
    build_detailed_appendix,
    build_executive_summary,
    build_management_summary,
    build_pdf_template_data,
    build_recommended_roadmap,
)
from app.services.site_profile import build_site_profile
from app.utils.helpers import format_percentage


def _collect_user_headings(pages: list[dict]) -> list[str]:
    collected = []
    seen = set()

    for page in pages:
        candidates = [
            page.get("title", ""),
            *page.get("headings", {}).get("h1", []),
            *page.get("headings", {}).get("h2", []),
            *page.get("headings", {}).get("h3", []),
        ]

        for candidate in candidates:
            cleaned_candidate = " ".join(str(candidate).split()).strip()
            if not cleaned_candidate:
                continue

            normalized_candidate = cleaned_candidate.lower()
            if normalized_candidate in seen:
                continue

            seen.add(normalized_candidate)
            collected.append(cleaned_candidate)

    return collected


def _status_label(resource: dict, fallback_text: str) -> str:
    status_code = resource.get("status_code", 0)

    if resource.get("exists"):
        return f"Found ({status_code})"
    if status_code:
        return f"{fallback_text} ({status_code})"
    return f"{fallback_text} (unreachable)"


def _sitemap_status_label(crawl_data: dict) -> str:
    sitemap_resource = crawl_data.get("sitemap", {})
    declared_sitemaps = crawl_data.get("declared_sitemaps", [])

    if sitemap_resource.get("exists"):
        return f"Found ({sitemap_resource.get('status_code', 200)})"
    if declared_sitemaps:
        return f"Declared in robots.txt ({len(declared_sitemaps)})"
    return _status_label(sitemap_resource, "Missing")


async def analyze_url(url: str):
    logger.info(f"Starting report generation for URL: {url}")

    crawl_data = await crawl_site(url)
    pages = crawl_data.get("pages", [])

    if not pages:
        logger.error("No crawlable HTML pages were returned from the crawl.")
        return {
            "error": (
                "The site could not be crawled successfully. "
                "It may be blocking requests, serving non-HTML content, or responding too slowly."
            )
        }

    primary_page = crawl_data.get("primary_page", pages[0])
    logger.info(
        f"Crawl completed with {crawl_data.get('analyzed_pages', 0)} sampled pages and "
        f"{crawl_data.get('discovered_internal_pages', 0)} discovered internal URLs."
    )

    primary_page_audit = audit_seo(primary_page, page_url=primary_page.get("url", ""))
    page_audits = [audit_seo(page, page_url=page.get("url", "")) for page in pages]
    sitewide_audit = audit_sitewide(crawl_data, page_audits)
    logger.info(f"Sitewide SEO health score: {sitewide_audit.get('overall_score')}")

    ai_result = generate_seo_suggestions(primary_page)
    site_profile = build_site_profile(url, primary_page, ai_result)
    logger.info(f"Dynamic site profile prepared for: {site_profile.get('company_name')}")

    fallback_text = " ".join(
        item
        for item in [
            primary_page.get("title", ""),
            primary_page.get("description", ""),
            *primary_page.get("headings", {}).get("h1", []),
            *primary_page.get("headings", {}).get("h2", [])[:3],
        ]
        if item
    )
    main_keyword = extract_main_keyword(ai_result, fallback_text)
    if not main_keyword:
        focus_keywords = site_profile.get("market_focus_keywords", [])
        main_keyword = focus_keywords[0] if focus_keywords else ""
    logger.info(f"Primary market keyword: {main_keyword or 'unavailable'}")

    competitors = await get_top_competitors(main_keyword)
    logger.info(f"Found {len(competitors)} competitors for comparison")

    user_headings = _collect_user_headings(pages)
    all_competitor_headings = []

    if competitors:
        competitor_heading_sets = await asyncio.gather(
            *(get_page_headings(competitor) for competitor in competitors)
        )

        for heading_set in competitor_heading_sets:
            all_competitor_headings.extend(heading_set)

    comparison_result = compare_with_competitors(
        user_headings=user_headings,
        competitor_headings=all_competitor_headings,
        seed_keyword=main_keyword,
        site_profile=site_profile,
    )
    logger.info("Competitor comparison completed")

    data_limitations = build_data_limitations(crawl_data)
    management_summary = build_management_summary(
        sitewide_audit,
        comparison_result,
        site_profile,
        crawl_data,
    )
    executive_summary = build_executive_summary(
        sitewide_audit,
        comparison_result,
        site_profile,
        management_summary,
    )
    recommended_roadmap = build_recommended_roadmap(sitewide_audit, comparison_result)
    detailed_appendix = build_detailed_appendix(
        crawl_data,
        primary_page_audit,
        sitewide_audit,
    )

    crawl_overview = {
        "analyzed_pages": crawl_data.get("analyzed_pages", 0),
        "discovered_internal_pages": crawl_data.get("discovered_internal_pages", 0),
        "sample_coverage_ratio": format_percentage(crawl_data.get("sample_coverage_ratio", 0.0)),
        "crawl_depth": crawl_data.get("crawl_depth", 0),
        "robots_txt_status": _status_label(crawl_data.get("robots", {}), "Missing"),
        "sitemap_status": _sitemap_status_label(crawl_data),
        "broken_internal_link_ratio": format_percentage(
            crawl_data.get("broken_link_summary", {}).get("broken_ratio", 0.0)
        ),
        "sampled_pages": sitewide_audit.get("page_summaries", []),
    }

    competitive_intelligence = {
        "keyword_overlap_score": comparison_result.get("keyword_overlap_score", "0%"),
        "content_gap_ratio": comparison_result.get("content_gap_ratio", "100%"),
        "competitor_sample_size": len(competitors),
        "market_opportunities": comparison_result.get("market_opportunities", []),
    }

    pdf_template_data = build_pdf_template_data(
        url=url,
        executive_summary=executive_summary,
        management_summary=management_summary,
        audit_result=sitewide_audit,
        comparison_result=comparison_result,
        crawl_data=crawl_data,
        site_profile=site_profile,
        data_limitations=data_limitations,
    )

    return {
        "executive_summary": executive_summary,
        "management_summary": management_summary,
        "crawl_overview": crawl_overview,
        "technical_audit": {
            "benchmark_reference_year": sitewide_audit.get("benchmark_reference_year"),
            "overall_seo_health": sitewide_audit.get("overall_seo_health"),
            "metric_summary": sitewide_audit.get("metric_summary", []),
            "findings": sitewide_audit.get("findings", []),
        },
        "competitive_intelligence": competitive_intelligence,
        "data_limitations": data_limitations,
        "recommended_roadmap": recommended_roadmap,
        "detailed_appendix": detailed_appendix,
        "pdf_template_data": pdf_template_data,
    }
