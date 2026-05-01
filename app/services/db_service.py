import traceback
from datetime import datetime, timezone
from typing import Any, Dict
from app.core.database import db_manager
from app.core.logger import logger
from bson import ObjectId

async def save_audit_report(url: str, business_type: str, result: Dict[str, Any]):
    """
    Splits the large SEO audit response into multiple structured MongoDB collections.
    Follows clean architecture by separating metadata, technical audit, AI insights, 
    SEO market data, and crawl details.
    """
    db = db_manager.database
    if db is None:
        logger.warning("Database not initialized or connection failed. Skipping save safely.")
        return None

    try:
        # 1. Prepare main 'projects' document
        # Extract numeric SEO health score (Primary: overall_score, Secondary: technical_audit.overall_seo_health)
        seo_score = result.get("overall_score")
        
        if seo_score is None:
            raw_health = result.get("technical_audit", {}).get("overall_seo_health", "0")
            try:
                seo_score = int(str(raw_health).replace("%", ""))
            except ValueError:
                seo_score = 0
        else:
            seo_score = int(seo_score)

        # If score is still 0, try to derive from metric_summary before saving
        if not seo_score:
            metric_summary = result.get("technical_audit", {}).get("metric_summary", [])
            derived = _score_from_metric_summary(metric_summary)
            if derived:
                seo_score = derived
                logger.info(f"Derived seo_score={seo_score} from metric_summary for {url}")

        project_doc = {
            "url": url,
            "business_type": business_type,
            "seo_score": seo_score,
            "report_url": result.get("report_url"),
            "created_at": datetime.now(timezone.utc)
        }
        
        # Insert project and get its ID
        project_result = await db.projects.insert_one(project_doc)
        project_id = project_result.inserted_id
        
        logger.info(f"Created project {project_id} for URL: {url}")

        # 2. Prepare 'audit_results' (Technical SEO)
        technical_audit = result.get("technical_audit", {})
        audit_doc = {
            "project_id": project_id,
            "overall_seo_health": seo_score,
            "metric_summary": technical_audit.get("metric_summary", []),
            "findings": technical_audit.get("findings", [])
        }
        await db.audit_results.insert_one(audit_doc)

        # 3. Prepare 'ai_insights' (AI + Business Layer)
        insights_doc = {
            "project_id": project_id,
            "executive_summary": result.get("executive_summary", ""),
            "management_summary": result.get("management_summary", {}),
            "recommended_roadmap": result.get("recommended_roadmap", []),
            "data_limitations": result.get("data_limitations", []),
            "insights": result.get("ai_insights", {}).get("insights", [])
        }
        await db.ai_insights.insert_one(insights_doc)

        # 4. Prepare 'seo_data' (Keywords + Competitors)
        seo_data_doc = {
            "project_id": project_id,
            "competitive_intelligence": result.get("competitive_intelligence", {}),
            "keyword_analysis": result.get("keyword_analysis", {})
        }
        await db.seo_data.insert_one(seo_data_doc)

        # 5. Prepare 'crawl_data' (Page-level info + Performance + Links)
        crawl_overview = result.get("crawl_overview", {})
        sampled_pages = list(crawl_overview.get("sampled_pages", []))

        crawl_doc = {
            "project_id": project_id,
            "crawl_overview": {
                "analyzed_pages": crawl_overview.get("analyzed_pages", 0),
                "discovered_internal_pages": crawl_overview.get("discovered_internal_pages", 0),
                "coverage_ratio": crawl_overview.get("sample_coverage_ratio", "0%"),
                "crawl_depth": crawl_overview.get("crawl_depth", 1),
                "robots_txt_status": crawl_overview.get("robots_txt_status", "Missing"),
                "sitemap_status": crawl_overview.get("sitemap_status", "Missing"),
                "favicon_status": crawl_overview.get("favicon_status", "Missing"),
                "domain_authority": crawl_overview.get("domain_authority", 0),
                "broken_internal_link_ratio": crawl_overview.get("broken_internal_link_ratio", "0%"),
            },
            "pages": sampled_pages,
            "page_speed": result.get("page_speed", {}),
            "link_analysis": result.get("link_analysis", {}),
            "content_strategy": result.get("content_strategy", {})
        }
        await db.crawl_data.insert_one(crawl_doc)

        logger.info(f"Successfully saved all audit components for project {project_id}")
        return project_id

    except Exception as e:
        logger.error(f"Error saving split audit data: {e}")
        raise e


def _score_from_metric_summary(metric_summary: list) -> int:
    """
    Derives a numeric SEO score from metric_summary status labels.
    Used as fallback for legacy records where overall_seo_health was saved as 0.
    Status mapping:
      'Good' / 'Pass' / 'Meets Standard'    -> 100 pts
      'Needs Work' / 'Improvement Needed'   -> 60 pts
      'Poor' / 'Critical Gap' / 'Fail'      -> 25 pts
    Returns 0 if no metrics available (no data case).
    """
    if not metric_summary:
        return 0
    total = 0
    for m in metric_summary:
        status = str(m.get("status", "")).lower()
        if any(k in status for k in ("good", "pass", "meets standard", "excellent")):
            total += 100
        elif any(k in status for k in ("needs work", "improvement", "moderate", "fair")):
            total += 60
        else:  # Critical Gap, Poor, Fail, Missing, etc.
            total += 25
    return int(round(total / len(metric_summary)))


async def get_all_projects():
    """
    Returns all analyzed projects enriched with audit + crawl summary data.
    For legacy records where seo_score=0, the real score is derived from
    audit_results.metric_summary status labels so all 61 projects appear
    with a meaningful score instead of 0.
    """
    db = db_manager.database
    if db is None:
        return []

    cursor = db.projects.find().sort("created_at", -1)
    projects = []
    async for doc in cursor:
        project_id = doc["_id"]
        doc["id"] = str(project_id)
        del doc["_id"]

        # Always fetch audit for counts + fallback score
        audit = await db.audit_results.find_one(
            {"project_id": project_id},
            {"overall_seo_health": 1, "findings": 1, "metric_summary": 1}
        )

        current_score = doc.get("seo_score", 0)
        if not current_score:
            # Try to recover score from audit_results
            if audit:
                raw = audit.get("overall_seo_health", 0)
                try:
                    recovered = int(str(raw).replace("%", ""))
                except (ValueError, TypeError):
                    recovered = 0

                if not recovered:
                    # Fall back to deriving score from metric statuses
                    recovered = _score_from_metric_summary(audit.get("metric_summary", []))

                doc["seo_score"] = recovered
            else:
                doc["seo_score"] = 0

        if audit:
            doc["findings_count"] = len(audit.get("findings", []))
            doc["metrics_count"] = len(audit.get("metric_summary", []))
        else:
            doc["findings_count"] = 0
            doc["metrics_count"] = 0

        # Enrich: pull crawl overview for page count
        crawl = await db.crawl_data.find_one(
            {"project_id": project_id},
            {"crawl_overview": 1}
        )
        if crawl:
            overview = crawl.get("crawl_overview", {})
            doc["pages_analyzed"] = overview.get("analyzed_pages", 0)
            doc["pages_discovered"] = overview.get("discovered_internal_pages", 0)
            doc["robots_status"] = overview.get("robots_txt_status") or "—"
            doc["sitemap_status"] = overview.get("sitemap_status") or "—"
        else:
            doc["pages_analyzed"] = 0
            doc["pages_discovered"] = 0
            doc["robots_status"] = "—"
            doc["sitemap_status"] = "—"

        projects.append(doc)

    return projects


def _normalize_page_for_frontend(page: dict) -> dict:
    """
    Flattens a page record to the flat shape the frontend Sampled Pages table expects:
      url, title_length, meta_description_length, word_count, h1_count, is_indexable

    Handles two stored formats:
      A) Legacy compact  - {url, seo_health, canonical_url, dofollow_links, ...}
      B) Rich summary    - {url, page_info:{title, meta_description}, headings:{h1_count},
                             content:{word_count}, technical_seo:{...}}
    """
    url = page.get("url", "")

    # ── Title length ──────────────────────────────────────────────────────────
    title_length = page.get("title_length")  # already flat? (future-proof)
    if title_length is None:
        title = page.get("page_info", {}).get("title") or page.get("title", "")
        title_length = len(str(title)) if title and title not in ("N/A", "") else None

    # ── Meta description length ───────────────────────────────────────────────
    meta_len = page.get("meta_description_length")  # already flat?
    if meta_len is None:
        meta = page.get("page_info", {}).get("meta_description") or page.get("description", "")
        meta_len = len(str(meta)) if meta and meta not in ("Not Found", "") else None

    # ── Word count ────────────────────────────────────────────────────────────
    word_count = page.get("word_count")  # already flat?
    if word_count is None:
        word_count = page.get("content", {}).get("word_count")  # rich summary

    # ── H1 count ─────────────────────────────────────────────────────────────
    h1_count = page.get("h1_count")  # already flat?
    if h1_count is None:
        h1_count = page.get("headings", {}).get("h1_count")  # rich summary
    if h1_count is None and "headings" in page:
        # headings might store h1 as a list
        h1_list = page.get("headings", {}).get("h1", [])
        if isinstance(h1_list, list):
            h1_count = len(h1_list)

    # ── Indexable ─────────────────────────────────────────────────────────────
    is_indexable = page.get("is_indexable")  # already flat?
    if is_indexable is None:
        indexing_status = page.get("page_info", {}).get("indexing_status", "")
        if indexing_status:
            is_indexable = indexing_status.lower() != "noindex"
        else:
            # Derive from technical_seo if available
            tech = page.get("technical_seo", {})
            if tech:
                is_indexable = True  # assume indexable unless explicit noindex

    # ── SEO health / score ────────────────────────────────────────────────────
    seo_health = page.get("seo_health") or f"{page.get('seo_score', '')}%" if page.get("seo_score") else None

    # ── Indexing Status ───────────────────────────────────────────────────────
    indexing_status = page.get("page_info", {}).get("indexing_status")
    if not indexing_status:
        indexing_status = "Indexable" if is_indexable else "Noindex"

    return {
        "url": url,
        "title_length": title_length,
        "meta_description_length": meta_len,
        "word_count": word_count,
        "h1_count": h1_count,
        "is_indexable": is_indexable,
        "indexing_status": indexing_status,
        "seo_health": seo_health,
        # Pass through any extra fields that future frontend versions may use
        "page_info": page.get("page_info", {}),
        "canonical_url": page.get("page_info", {}).get("canonical") or page.get("canonical_url"),
    }


async def get_project_audit(project_id_str: str) -> Dict[str, Any] | None:
    """
    Retrieves and aggregates all audit components for a given project ID.
    """
    db = db_manager.database
    if db is None:
        return None

    try:
        project_id = ObjectId(project_id_str)
        
        # Fetch data from all collections
        project = await db.projects.find_one({"_id": project_id})
        if not project:
            return None

        # Fetch sub-documents; handle cases where they might be missing gracefully
        audit_results = await db.audit_results.find_one({"project_id": project_id}) or {}
        ai_insights = await db.ai_insights.find_one({"project_id": project_id}) or {}
        seo_data = await db.seo_data.find_one({"project_id": project_id}) or {}
        crawl_data = await db.crawl_data.find_one({"project_id": project_id}) or {}

        # Reconstruct the FinalResponse structure
        # Ensure we don't crash on missing sub-docs by providing defaults
        result = {
            "url": project.get("url", ""),
            "overall_score": project.get("seo_score", 0),
            "seo_health": f"{project.get('seo_score', 0)}%",
            "site_favicon": project.get("site_favicon", {"status": "Missing", "url": "", "source": "fallback"}),
            "executive_summary": ai_insights.get("executive_summary", ""),
            "management_summary": ai_insights.get("management_summary", {}),
            "recommended_roadmap": ai_insights.get("recommended_roadmap", []),
            "data_limitations": ai_insights.get("data_limitations", []),
            "technical_audit": {
                "benchmark_reference_year": audit_results.get("benchmark_reference_year", 2026),
                "overall_seo_health": f"{audit_results.get('overall_seo_health', project.get('seo_score', 0))}%",
                "metric_summary": audit_results.get("metric_summary", []),
                "findings": audit_results.get("findings", []),
                "score_breakdown": audit_results.get("score_breakdown", [])
            },
            "competitive_intelligence": seo_data.get("competitive_intelligence", {
                "keyword_overlap_score": "0%",
                "content_gap_ratio": "100%",
                "competitor_sample_size": 0,
                "market_opportunities": []
            }),
            "keyword_analysis": seo_data.get("keyword_analysis", {
                "primary_keywords": [],
                "long_tail_keywords": [],
                "keyword_intent": {"informational": [], "transactional": [], "navigational": []}
            }),
            "crawl_overview": {
                "analyzed_pages": crawl_data.get("crawl_overview", {}).get("analyzed_pages", 0),
                "discovered_internal_pages": crawl_data.get("crawl_overview", {}).get("discovered_internal_pages", 0),
                "sample_coverage_ratio": crawl_data.get("crawl_overview", {}).get("sample_coverage_ratio", "0%"),
                "crawl_depth": crawl_data.get("crawl_overview", {}).get("crawl_depth", 1),
                "robots_txt_status": crawl_data.get("crawl_overview", {}).get("robots_txt_status", "Missing"),
                "sitemap_status": crawl_data.get("crawl_overview", {}).get("sitemap_status", "Missing"),
                "favicon_status": crawl_data.get("crawl_overview", {}).get("favicon_status", "Missing"),
                "domain_authority": crawl_data.get("crawl_overview", {}).get("domain_authority", 0),
                "broken_internal_link_ratio": crawl_data.get("crawl_overview", {}).get("broken_internal_link_ratio", "0%"),
                "sampled_pages": [_normalize_page_for_frontend(p) for p in crawl_data.get("pages", [])]
            },
            "page_speed": crawl_data.get("page_speed", {"score": 0, "status": "N/A", "response_time": 0.0, "page_size_kb": 0.0}),
            "link_analysis": crawl_data.get("link_analysis", {
                "internal": {"internal_link_score": 0, "issues": [], "recommendations": []},
                "external": {"total_external_links": 0, "domains": []},
                "backlinks": {"backlink_strength": "Unknown", "estimated_backlinks": 0, "referring_domains": 0}
            }),
            "content_strategy": crawl_data.get("content_strategy", {"blog_suggestions": [], "guest_post_titles": []}),
            "ai_insights": {"insights": ai_insights.get("insights", [])},
            "report_url": project.get("report_url"),
            "status": "completed"
        }

        return result

    except Exception as e:
        logger.error(f"Error retrieving audit data for {project_id_str}: {e}\n{traceback.format_exc()}")
        return None


async def delete_project(project_id_str: str) -> bool:
    """
    Deletes a project and all its associated data from MongoDB collections.
    """
    db = db_manager.database
    if db is None:
        return False

    try:
        project_id = ObjectId(project_id_str)
        
        # 1. Delete from sub-collections first
        await db.audit_results.delete_many({"project_id": project_id})
        await db.ai_insights.delete_many({"project_id": project_id})
        await db.seo_data.delete_many({"project_id": project_id})
        await db.crawl_data.delete_many({"project_id": project_id})
        
        # 2. Finally delete the main project document
        result = await db.projects.delete_one({"_id": project_id})
        
        if result.deleted_count > 0:
            logger.info(f"Successfully deleted project {project_id_str} and all its data")
            return True
        else:
            logger.warning(f"Project {project_id_str} not found in projects collection during deletion")
            return False

    except Exception as e:
        logger.error(f"Error deleting project {project_id_str}: {e}\n{traceback.format_exc()}")
        return False

