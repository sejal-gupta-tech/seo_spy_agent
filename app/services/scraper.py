import asyncio
import contextlib
import time
import traceback

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


def _status_label(resource_data: dict, default="Missing") -> str:
    if not resource_data:
        return default
    if resource_data.get("exists"):
        status = resource_data.get("status_code", "Unknown")
        return f"Found ({status})"
    return "Missing"


def _sitemap_status_label(crawl_data: dict) -> str:
    sitemap = crawl_data.get("sitemap", {})
    if sitemap.get("exists"):
        status = sitemap.get("status_code", "Unknown")
        url_count = len(sitemap.get("urls", []))
        return f"Found ({status}) - {url_count} URLs"
    return "Missing"


def _favicon_status_label(crawl_data: dict) -> str:
    primary_page = crawl_data.get("primary_page", {})
    
    # has_favicon is only True when a standard rel="icon" or rel="shortcut icon"
    # link tag was found with a non-empty, non-data-URI href.
    # apple-touch-icon and mask-icon are explicitly excluded by the crawler.
    if primary_page.get("has_favicon") and primary_page.get("favicon_url"):
        return "Found (HTML link tag)"

    favicon_resource = crawl_data.get("favicon", {})
    if favicon_resource.get("exists") and favicon_resource.get("status_code") == 200:
        return f"Found (/favicon.ico · {favicon_resource.get('status_code')})"

    return _status_label(favicon_resource, "Missing")


class SEOAuditPipeline:
    """Modular pipeline for executing a full SEO audit."""

    def __init__(self, url: str, progress_callback: ProgressCallback | None = None):
        self.url = url
        self.progress_callback = progress_callback
        self.start_time = time.perf_counter()
        
        # State
        self.crawl_data = {}
        self.pages = []
        self.page_speed_data = {}
        self.sitewide_audit = {}
        self.ai_result = {}
        self.site_profile = {}
        self.competitors = []
        self.comparison_result = {}
        self.keyword_data = {}
        self.ai_insights = {}
        self.blog_suggestions = {}
        self.guest_posts = {}

    async def emit(self, event: dict) -> None:
        """Emit progress updates with elapsed time."""
        event.setdefault("elapsed_seconds", round(time.perf_counter() - self.start_time, 2))
        await emit_progress(self.progress_callback, event)

    async def _crawl_stage(self):
        """Phase 1: Initial Crawl and Page Speed Analysis."""
        await self.emit({
            "type": "stage", "stage": "crawl", "status": "active",
            "label": "Mapping crawl frontier",
            "detail": "Collecting HTML pages and performance signals."
        })

        from app.services.page_speed import get_page_speed
        page_speed_task = asyncio.create_task(get_page_speed(self.url))

        try:
            self.crawl_data = await crawl_site(self.url, progress_callback=self.progress_callback)
            self.pages = self.crawl_data.get("pages", [])
            self.page_speed_data = await page_speed_task
        except Exception as e:
            logger.error(f"Crawl stage failed: {e}")
            if not page_speed_task.done():
                page_speed_task.cancel()
            raise

        if not self.pages:
            raise ValueError("The site could not be crawled successfully.")

        # Parallel URL Structure Analysis
        from app.services.url_analysis import analyze_url_structure
        for page in self.pages:
            if "url" in page:
                page["url_structure"] = analyze_url_structure(page["url"])

        await self.emit({
            "type": "stage", "stage": "crawl", "status": "completed",
            "label": "Mapping crawl frontier",
            "detail": f"Captured {len(self.pages)} pages."
        })

    async def _audit_stage(self):
        """Phase 2: Technical SEO Audit."""
        await self.emit({
            "type": "stage", "stage": "audit", "status": "active",
            "label": "Scoring technical health",
            "detail": "Analyzing titles, headings, and mobile readiness."
        })

        # Enrich pages with performance data
        perf_score = self.page_speed_data.get("score", 100.0)
        for page in self.pages:
            page["performance_score"] = perf_score

        # Parallelize individual page audits using ThreadPool (since audit_seo is sync)
        loop = asyncio.get_event_loop()
        audit_tasks = [
            loop.run_in_executor(None, audit_seo, page, page.get("url", ""))
            for page in self.pages
        ]
        page_audits = await asyncio.gather(*audit_tasks)

        self.sitewide_audit = audit_sitewide(self.crawl_data, page_audits, self.page_speed_data)
        
        await self.emit({
            "type": "health_snapshot",
            "overall_score": self.sitewide_audit.get("overall_score", 0),
            "overall_seo_health": self.sitewide_audit.get("overall_seo_health", "0%"),
            "metric_summary": self.sitewide_audit.get("metric_summary", [])[:4],
        })

        for finding in self.sitewide_audit.get("findings", [])[:6]:
            await self.emit({"type": "finding", "finding": finding})

    async def _ai_strategy_stage(self):
        """Phase 3: AI-Driven Insights and Strategy."""
        await self.emit({
            "type": "stage", "stage": "ai", "status": "active",
            "label": "Running AI strategy passes",
            "detail": "Generating keyword themes and rewrite angles."
        })
        
        primary_page = self.crawl_data.get("primary_page", self.pages[0])
        
        # Start AI suggestions
        self.ai_result = await asyncio.to_thread(generate_seo_suggestions, primary_page)
        self.site_profile = build_site_profile(self.url, primary_page, self.ai_result)
        
        # Parallel content strategy
        from app.services.content_strategy import generate_blog_suggestions, generate_guest_post_titles
        blog_task = asyncio.to_thread(generate_blog_suggestions, primary_page, self.ai_result)
        guest_task = asyncio.to_thread(generate_guest_post_titles, primary_page, self.ai_result)
        
        self.blog_suggestions, self.guest_posts = await asyncio.gather(blog_task, guest_task)

    async def _competition_stage(self):
        """Phase 4: Competitor Analysis."""
        await self.emit({
            "type": "stage", "stage": "competition", "status": "active",
            "label": "Comparing market coverage",
            "detail": "Searching competitors and extracting their heading coverage."
        })
        
        primary_page = self.crawl_data.get("primary_page", self.pages[0])
        fallback_text = f"{primary_page.get('title', '')} {primary_page.get('description', '')}"
        main_keyword = extract_main_keyword(self.ai_result, fallback_text)
        
        self.competitors = await get_top_competitors(main_keyword)
        
        # Parallel Competitor Heading Extraction
        if self.competitors:
            competitor_heading_sets = await asyncio.gather(
                *(get_page_headings(comp) for comp in self.competitors)
            )
            all_comp_headings = [h for s in competitor_heading_sets for h in s]
        else:
            all_comp_headings = []

        # Complex Analysis Tasks in parallel
        from app.services.keyword_analysis import generate_relevant_keywords
        from app.services.ai_insights import get_ai_insights

        tasks = [
            asyncio.to_thread(compare_with_competitors, _collect_user_headings(self.pages), all_comp_headings, main_keyword, self.site_profile),
            asyncio.to_thread(generate_relevant_keywords, primary_page, self.ai_result.get("keywords", [])),
            asyncio.to_thread(get_ai_insights, self.sitewide_audit)
        ]
        self.comparison_result, self.keyword_data, self.ai_insights = await asyncio.gather(*tasks)

    async def _report_stage(self):
        """Phase 5: Report Generation."""
        await self.emit({
            "type": "stage", "stage": "report", "status": "active",
            "label": "Rendering final report",
            "detail": "Composing the executive narrative and PDF export."
        })
        
        # Assembly logic
        self.data_limitations = build_data_limitations(self.crawl_data)
        self.management_summary = build_management_summary(self.sitewide_audit, self.comparison_result, self.site_profile, self.crawl_data)
        self.executive_summary = build_executive_summary(self.sitewide_audit, self.comparison_result, self.site_profile, self.management_summary)
        self.recommended_roadmap = build_recommended_roadmap(self.sitewide_audit, self.comparison_result)
        self.detailed_appendix = build_detailed_appendix(self.crawl_data, {}, self.sitewide_audit)

        from app.services.report_generator import save_report_to_file
        self.pdf_template_data = build_pdf_template_data(
            self.url, self.site_profile, self.management_summary, self.executive_summary,
            self.recommended_roadmap, self.detailed_appendix, self.data_limitations
        )
        self.final_report_id = save_report_to_file(self.pdf_template_data)

    async def execute(self) -> dict:
        """Run the full pipeline."""
        try:
            await self._crawl_stage()
            await self._audit_stage()
            await self._ai_strategy_stage()
            await self._competition_stage()
            await self._report_stage()
            
            return self._assemble_final_result()
        except Exception as e:
            logger.error(f"Audit Pipeline failed: {e}\n{traceback.format_exc()}")
            return {"error": str(e)}

    def _assemble_final_result(self) -> dict:
        """Final data assembly."""
        from app.services.authority import calculate_domain_authority, calculate_page_authority
        for page in self.pages:
            page["page_authority"] = calculate_page_authority(page)
            
        competitive_intelligence = {
            "keyword_overlap_score": self.comparison_result.get("keyword_overlap_score", "0%"),
            "content_gap_ratio": self.comparison_result.get("content_gap_ratio", "100%"),
            "competitor_sample_size": len(self.competitors),
            "market_opportunities": self.comparison_result.get("market_opportunities", []),
        }
            
        return {
            "url": self.url,
            "overall_score": self.sitewide_audit.get("overall_score", 0),
            "seo_health": self.sitewide_audit.get("overall_seo_health", "0%"),
            "site_profile": self.site_profile,
            "crawl_overview": {
                "analyzed_pages": len(self.pages),
                "discovered_internal_pages": self.crawl_data.get("discovered_internal_pages", 0),
                "sample_coverage_ratio": format_percentage(self.crawl_data.get("sample_coverage_ratio", 0.0)),
                "robots_txt_status": self.crawl_data.get("robots", {}).get("status_string", "Missing"),
                "sitemap_status": _sitemap_status_label(self.crawl_data),
                "favicon_status": _favicon_status_label(self.crawl_data),
                "domain_authority": calculate_domain_authority(self.pages),
                "sampled_pages": self.sitewide_audit.get("page_summaries", []),
            },
            "technical_audit": {
                "benchmark_reference_year": self.sitewide_audit.get("benchmark_reference_year"),
                "overall_seo_health": self.sitewide_audit.get("overall_seo_health"),
                "metric_summary": self.sitewide_audit.get("metric_summary", []),
                "findings": self.sitewide_audit.get("findings", []),
                "score_breakdown": self.sitewide_audit.get("score_breakdown", []),
            },
            "executive_summary": self.executive_summary,
            "management_summary": self.management_summary,
            "recommended_roadmap": self.recommended_roadmap,
            "detailed_appendix": self.detailed_appendix,
            "data_limitations": self.data_limitations,
            "competitive_intelligence": competitive_intelligence,
            "content_strategy": {
                "blog_suggestions": self.blog_suggestions.get("blog_posts", []),
                "guest_post_titles": self.guest_posts.get("guest_post_titles", [])
            },
            "keyword_analysis": self.keyword_data,
            "ai_insights": self.ai_insights,
            "page_speed": self.page_speed_data,
            "report_url": f"/download-report/{self.final_report_id}",
            "status": "completed"
        }

async def analyze_url(url: str, progress_callback: ProgressCallback | None = None):
    pipeline = SEOAuditPipeline(url, progress_callback)
    return await pipeline.execute()
