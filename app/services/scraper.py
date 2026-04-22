import asyncio
import time

from app.core.logger import logger
from app.services.progress import ProgressCallback, emit_progress
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

    if sitemap_resource.get("exists") and sitemap_resource.get("status_string") == "Found (Valid)":
        return "Found (Valid)"
    if declared_sitemaps:
        return f"Declared in robots.txt ({len(declared_sitemaps)})"
    return sitemap_resource.get("status_string", "Missing")


def _favicon_status_label(crawl_data: dict) -> str:
    primary_page = crawl_data.get("primary_page", {})
    if primary_page.get("has_favicon"):
        return "Found (HTML meta tag)"
    
    favicon_resource = crawl_data.get("favicon", {})
    if favicon_resource.get("exists"):
        return f"Found (/{favicon_resource.get('status_code', 200)})"
        
    return _status_label(favicon_resource, "Missing")


async def analyze_url(
    url: str,
    progress_callback: ProgressCallback | None = None,
):
    logger.info(f"Starting report generation for URL: {url}")
    request_started_at = time.perf_counter()

    async def emit(event: dict) -> None:
        event.setdefault(
            "elapsed_seconds",
            round(time.perf_counter() - request_started_at, 2),
        )
        await emit_progress(progress_callback, event)

    await emit(
        {
            "type": "run_started",
            "url": url,
            "message": "Initializing crawl frontier and benchmark pipeline.",
        }
    )
    await emit(
        {
            "type": "stage",
            "stage": "crawl",
            "status": "active",
            "label": "Mapping crawl frontier",
            "detail": "Collecting HTML pages, depth, and internal link signals.",
        }
    )

    from app.services.page_speed import get_page_speed
    page_speed_task = asyncio.create_task(get_page_speed(url))
    crawl_data = await crawl_site(url, progress_callback=progress_callback)
    logger.info(f"Crawl stage completed in {time.perf_counter() - request_started_at:.2f}s")
    await emit(
        {
            "type": "stage",
            "stage": "crawl",
            "status": "completed",
            "label": "Mapping crawl frontier",
            "detail": (
                f"Captured {crawl_data.get('analyzed_pages', 0)} pages and "
                f"{crawl_data.get('discovered_internal_pages', 0)} discovered URLs."
            ),
        }
    )
    pages = crawl_data.get("pages", [])
    
    from app.services.url_analysis import analyze_url_structure
    for page in pages:
        if "url" in page:
            page["url_structure"] = analyze_url_structure(page["url"])

    if not pages:
        logger.error("No crawlable HTML pages were returned from the crawl.")
        await emit(
            {
                "type": "error",
                "detail": (
                    "The site could not be crawled successfully. "
                    "It may be blocking requests, serving non-HTML content, or responding too slowly."
                ),
            }
        )
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

    await emit(
        {
            "type": "stage",
            "stage": "audit",
            "status": "active",
            "label": "Scoring technical health",
            "detail": "Checking titles, canonicals, headings, page speed, and link quality.",
        }
    )

    primary_page_audit = audit_seo(primary_page, page_url=primary_page.get("url", ""))
    page_audits = [audit_seo(page, page_url=page.get("url", "")) for page in pages]
    page_speed_data = await page_speed_task
    logger.info(f"Page speed stage completed in {time.perf_counter() - request_started_at:.2f}s")

    sitewide_audit = audit_sitewide(crawl_data, page_audits, page_speed_data)
    logger.info(f"Sitewide SEO health score: {sitewide_audit.get('overall_score')}")
    await emit(
        {
            "type": "health_snapshot",
            "overall_score": sitewide_audit.get("overall_score", 0),
            "overall_seo_health": sitewide_audit.get("overall_seo_health", "0%"),
            "analyzed_pages": crawl_data.get("analyzed_pages", 0),
            "discovered_internal_pages": crawl_data.get("discovered_internal_pages", 0),
            "sample_coverage_ratio": crawl_data.get("sample_coverage_ratio", 0.0),
            "metric_summary": sitewide_audit.get("metric_summary", [])[:4],
        }
    )

    for finding in sitewide_audit.get("findings", [])[:6]:
        await emit({"type": "finding", "finding": finding})

    await emit(
        {
            "type": "stage",
            "stage": "audit",
            "status": "completed",
            "label": "Scoring technical health",
            "detail": f"Signal now reads {sitewide_audit.get('overall_seo_health', '0%')}.",
        }
    )

    await emit(
        {
            "type": "stage",
            "stage": "ai",
            "status": "active",
            "label": "Running AI strategy passes",
            "detail": "Generating keyword themes, rewrite angles, and board-facing notes.",
        }
    )

    await emit(
        {
            "type": "ai_update",
            "label": "Primary page model",
            "detail": "Extracting page-level SEO keywords and metadata opportunities.",
        }
    )
    ai_result = await asyncio.to_thread(generate_seo_suggestions, primary_page)
    site_profile = build_site_profile(url, primary_page, ai_result)
    logger.info(f"Dynamic site profile prepared for: {site_profile.get('company_name')}")
    await emit(
        {
            "type": "ai_update",
            "label": "Site profile inferred",
            "detail": (
                f"Brand context shaped around {site_profile.get('company_name', 'the website')}."
            ),
        }
    )

    from app.services.content_strategy import generate_blog_suggestions, generate_guest_post_titles
    await emit(
        {
            "type": "ai_update",
            "label": "Content strategy model",
            "detail": "Generating blog angles and guest post opportunities.",
        }
    )
    blog_suggestions = await asyncio.to_thread(generate_blog_suggestions, primary_page, ai_result)
    guest_posts = await asyncio.to_thread(generate_guest_post_titles, primary_page, ai_result)
    logger.info("Content Strategy Generation completed via OpenAI")
    await emit(
        {
            "type": "stage",
            "stage": "ai",
            "status": "completed",
            "label": "Running AI strategy passes",
            "detail": "Content strategy and rewrite angles are now in memory.",
        }
    )

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

    await emit(
        {
            "type": "stage",
            "stage": "competition",
            "status": "active",
            "label": "Comparing market coverage",
            "detail": "Searching competitors and extracting their heading coverage.",
        }
    )
    competitors = await get_top_competitors(main_keyword)
    logger.info(f"Found {len(competitors)} competitors for comparison")
    await emit(
        {
            "type": "competitor_update",
            "phase": "search",
            "count": len(competitors),
            "competitors": competitors,
        }
    )

    user_headings = _collect_user_headings(pages)
    all_competitor_headings = []

    if competitors:
        await emit(
            {
                "type": "competitor_update",
                "phase": "heading-fetch",
                "count": len(competitors),
                "competitors": competitors,
            }
        )
        competitor_heading_sets = await asyncio.gather(
            *(get_page_headings(competitor) for competitor in competitors)
        )

        for heading_set in competitor_heading_sets:
            all_competitor_headings.extend(heading_set)

    from app.services.keyword_analysis import generate_relevant_keywords
    from app.services.ai_insights import get_ai_insights

    comparison_task = asyncio.to_thread(
        compare_with_competitors,
        user_headings=user_headings,
        competitor_headings=all_competitor_headings,
        seed_keyword=main_keyword,
        site_profile=site_profile,
    )
    keyword_analysis_task = asyncio.to_thread(
        generate_relevant_keywords,
        primary_page,
        ai_result.get("keywords", []),
    )
    ai_insights_task = asyncio.to_thread(get_ai_insights, sitewide_audit)

    comparison_result, keyword_analysis_data, ai_insights_data = await asyncio.gather(
        comparison_task,
        keyword_analysis_task,
        ai_insights_task,
    )
    logger.info("Competitor comparison completed")

    for opportunity in comparison_result.get("market_opportunities", [])[:5]:
        await emit({"type": "opportunity", "opportunity": opportunity})

    await emit(
        {
            "type": "stage",
            "stage": "competition",
            "status": "completed",
            "label": "Comparing market coverage",
            "detail": (
                f"Comparison finished across {len(competitors)} competitor domains."
            ),
        }
    )

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

    from app.services.authority import calculate_domain_authority, calculate_page_authority

    # Enrich each page with Page Authority
    for page in pages:
        page["page_authority"] = calculate_page_authority(page)

    domain_auth = calculate_domain_authority(pages)
    
    crawl_overview = {
        "analyzed_pages": crawl_data.get("analyzed_pages", 0),
        "discovered_internal_pages": crawl_data.get("discovered_internal_pages", 0),
        "sample_coverage_ratio": format_percentage(crawl_data.get("sample_coverage_ratio", 0.0)),
        "crawl_depth": crawl_data.get("crawl_depth", 0),
        "robots_txt_status": crawl_data.get("robots", {}).get("status_string", "Missing"),
        "sitemap_status": _sitemap_status_label(crawl_data),
        "favicon_status": _favicon_status_label(crawl_data),
        "domain_authority": domain_auth,
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

    if not keyword_analysis_data.get("primary_keywords"):
        sitewide_audit.setdefault("findings", []).append({
            "category": "Content Strategy",
            "metric": "AI Keyword Extraction",
            "current_value": "No relevant keywords detected.",
            "benchmark": "2026 standard: At least 3 targeted semantic core terms.",
            "score": 0,
            "business_impact": "Absence of discoverable semantic targeting prevents ranking velocity for any navigational or transactional SERP clusters.",
            "recommendation": "Rewrite page copy explicitly focusing on core commercial intent anchors.",
            "priority": "High",
            "evidence": []
        })

    from app.services.link_analysis import analyze_internal_linking, estimate_backlink_profile
    internal_link_report = analyze_internal_linking(pages)
    backlink_report = estimate_backlink_profile(pages)

    total_externals = sum(p.get("external_links_count", 0) for p in pages)
    ext_domains = set()
    for p in pages:
        ext_domains.update(p.get("external_domains", []))

    link_analysis_data = {
        "internal": internal_link_report,
        "external": {
            "total_external_links": total_externals,
            "domains": list(ext_domains)
        },
        "backlinks": backlink_report
    }

    from app.services.report_generator import render_report_html, generate_pdf_report

    await emit(
        {
            "type": "stage",
            "stage": "report",
            "status": "active",
            "label": "Rendering final report",
            "detail": "Composing the executive narrative and PDF export.",
        }
    )
    print("Generating HTML report...")

    html_content = render_report_html(pdf_template_data)
    await emit(
        {
            "type": "report_status",
            "label": "HTML report rendered",
            "detail": "Packaging the visual report layer for export.",
        }
    )

    print("Generating PDF report...")

    task_id = await asyncio.to_thread(generate_pdf_report, html_content)

    print("Task ID:", task_id)
    logger.info(f"Report generation completed in {time.perf_counter() - request_started_at:.2f}s")

    report_url = f"/download-report/{task_id}" if task_id else None
    await emit(
        {
            "type": "report_status",
            "label": "Export bundle ready",
            "detail": "PDF relay path generated for the frontend download action.",
            "report_url": report_url,
        }
    )
    await emit(
        {
            "type": "stage",
            "stage": "report",
            "status": "completed",
            "label": "Rendering final report",
            "detail": "The crawl, audit, and board report are complete.",
        }
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
        "content_strategy": {
            "blog_suggestions": blog_suggestions.get("blog_posts", []),
            "guest_post_titles": guest_posts.get("guest_post_titles", [])
        },
        "page_speed": page_speed_data,
        "keyword_analysis": keyword_analysis_data,
        "link_analysis": link_analysis_data,
        "ai_insights": ai_insights_data,
        "report_url": report_url
    }
