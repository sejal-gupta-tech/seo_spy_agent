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

        # Normalize URL for uniqueness checks (strip spaces, lowercase, remove trailing slash)
        normalized_url = url.strip().lower().rstrip("/")
        current_time = datetime.now(timezone.utc)
        
        # Check if project with this URL already exists to avoid duplicates
        existing_project = await db.projects.find_one({"url": normalized_url})
        
        if existing_project:
            project_id = existing_project["_id"]
            # Update existing project record
            await db.projects.update_one(
                {"_id": project_id},
                {
                    "$set": {
                        "seo_score": seo_score,
                        "report_url": result.get("report_url"),
                        "business_type": business_type,
                        "site_favicon": result.get("site_favicon"),
                        "updated_at": current_time
                    }
                }
            )
            logger.info(f"Updated existing project {project_id} for URL: {normalized_url}")
        else:
            # Create new project record
            project_doc = {
                "url": normalized_url,
                "business_type": business_type,
                "seo_score": seo_score,
                "report_url": result.get("report_url"),
                "site_favicon": result.get("site_favicon"),
                "created_at": current_time,
                "updated_at": current_time
            }
            project_result = await db.projects.insert_one(project_doc)
            project_id = project_result.inserted_id
            logger.info(f"Created new project {project_id} for URL: {normalized_url}")

        # 2. Prepare 'audit_results' (Technical SEO)
        technical_audit = result.get("technical_audit", {})
        audit_doc = {
            "project_id": project_id,
            "overall_seo_health": seo_score,
            "metric_summary": technical_audit.get("metric_summary", []),
            "findings": technical_audit.get("findings", []),
            "updated_at": current_time
        }
        await db.audit_results.update_one(
            {"project_id": project_id},
            {"$set": audit_doc},
            upsert=True
        )

        # 3. Prepare 'ai_insights' (AI + Business Layer)
        insights_doc = {
            "project_id": project_id,
            "executive_summary": result.get("executive_summary", ""),
            "management_summary": result.get("management_summary", {}),
            "recommended_roadmap": result.get("recommended_roadmap", []),
            "data_limitations": result.get("data_limitations", []),
            "insights": result.get("ai_insights", {}).get("insights", []),
            "updated_at": current_time
        }
        await db.ai_insights.update_one(
            {"project_id": project_id},
            {"$set": insights_doc},
            upsert=True
        )

        # 4. Prepare 'seo_data' (Keywords + Competitors)
        seo_data_doc = {
            "project_id": project_id,
            "competitive_intelligence": result.get("competitive_intelligence", {}),
            "keyword_analysis": result.get("keyword_analysis", {}),
            "updated_at": current_time
        }
        await db.seo_data.update_one(
            {"project_id": project_id},
            {"$set": seo_data_doc},
            upsert=True
        )

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
            "content_strategy": result.get("content_strategy", {}),
            "updated_at": current_time
        }
        await db.crawl_data.update_one(
            {"project_id": project_id},
            {"$set": crawl_doc},
            upsert=True
        )

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
    projects_raw = await cursor.to_list(length=None)
    
    if not projects_raw:
        return []

    project_ids = [doc["_id"] for doc in projects_raw]
    
    audit_cursor = db.audit_results.find(
        {"project_id": {"$in": project_ids}},
        {"project_id": 1, "overall_seo_health": 1, "findings": 1, "metric_summary": 1}
    )
    audits_map = {doc["project_id"]: doc async for doc in audit_cursor}

    crawl_cursor = db.crawl_data.find(
        {"project_id": {"$in": project_ids}},
        {"project_id": 1, "crawl_overview": 1}
    )
    crawls_map = {doc["project_id"]: doc async for doc in crawl_cursor}

    projects = []
    for doc in projects_raw:
        project_id = doc["_id"]
        doc["id"] = str(project_id)
        del doc["_id"]

        audit = audits_map.get(project_id)

        current_score = doc.get("seo_score", 0)
        if not current_score:
            if audit:
                raw = audit.get("overall_seo_health", 0)
                try:
                    recovered = int(str(raw).replace("%", ""))
                except (ValueError, TypeError):
                    recovered = 0

                if not recovered:
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

        crawl = crawls_map.get(project_id)
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

    # ── Headings logic ───────────────────────────────────────────────────────
    headings_obj = {
        "h1_count": 0, "h2_count": 0, "h3_count": 0, "h4_count": 0, "h5_count": 0, "h6_count": 0,
        "h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": [],
        "warnings": []
    }
    
    raw_headings = page.get("headings", {})
    if isinstance(raw_headings, dict):
        for index in range(1, 7):
            tag = f"h{index}"
            if tag in raw_headings and isinstance(raw_headings[tag], list):
                headings_obj[tag] = raw_headings[tag]
                headings_obj[f"{tag}_count"] = len(raw_headings[tag])
            elif f"{tag}_count" in raw_headings and raw_headings.get(f"{tag}_count") is not None:
                headings_obj[f"{tag}_count"] = raw_headings.get(f"{tag}_count")

    # Keep h1_content for legacy compatibility
    headings_obj["h1_content"] = headings_obj["h1"][0] if headings_obj["h1"] else raw_headings.get("h1_content", "Missing H1")

    if headings_obj["h1_count"] > 1:
        headings_obj["warnings"].append("Multiple H1 tags detected")
    elif headings_obj["h1_count"] == 0:
        headings_obj["warnings"].append("No H1 tag detected")
        
    h1_count = headings_obj["h1_count"]

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

    # ── Page-specific issues ──────────────────────────────────────────────────
    structured_issues = []
    
    # Title length check
    title = page.get("page_info", {}).get("title") or page.get("title", "")
    if not title or title == "N/A":
        structured_issues.append({
            "title": "Missing Page Title",
            "severity": "High",
            "why_it_matters": "Search engines use H1 tags to understand the primary topic of a page. Users rely on them for visual hierarchy.",
            "recommended_fix": "Add exactly one descriptive H1 tag containing the main target keyword near the top of the page.",
            "seo_impact": "Improves content relevance, keyword targeting, and search engine understanding."
        })
        # Note: Fixing copy to match Title tag
        structured_issues[-1] = {
            "title": "Missing Page Title",
            "severity": "High",
            "why_it_matters": "The page title is the most important on-page SEO element. Without it, search engines struggle to understand what the page is about.",
            "recommended_fix": "Add a descriptive, keyword-optimized <title> tag between 15-60 characters.",
            "seo_impact": "Massively improves search visibility and click-through rates."
        }
    elif len(title) < 15:
        structured_issues.append({
            "title": "Title Too Short",
            "severity": "Medium",
            "why_it_matters": "A very short title fails to fully describe the page and misses opportunities to target secondary keywords.",
            "recommended_fix": "Expand the title tag to 40-60 characters by adding relevant descriptive words or brand name.",
            "seo_impact": "Helps capture more long-tail search traffic."
        })
    elif len(title) > 60:
        structured_issues.append({
            "title": "Title Too Long",
            "severity": "Low",
            "why_it_matters": "Titles over 60 characters get cut off (truncated) in Google search results, reducing click-through rates.",
            "recommended_fix": "Shorten the title to under 60 characters, keeping the most important keywords near the beginning.",
            "seo_impact": "Improves readability and click-through rate in search results."
        })
    
    # Meta description check
    meta = page.get("page_info", {}).get("meta_description") or page.get("description", "")
    if not meta or meta == "Not Found":
        structured_issues.append({
            "title": "Missing Meta Description",
            "severity": "High",
            "why_it_matters": "Meta descriptions are your sales pitch in the search results. Without one, Google will pick random text from the page.",
            "recommended_fix": "Write a compelling meta description summarizing the page content (between 120-160 characters).",
            "seo_impact": "Directly improves organic click-through rates (CTR)."
        })
    elif len(meta) < 50:
        structured_issues.append({
            "title": "Meta Description Too Short",
            "severity": "Medium",
            "why_it_matters": "Short descriptions don't give users enough compelling reasons to click your link instead of a competitor's.",
            "recommended_fix": "Expand the meta description to include a clear call-to-action and more details (aim for 120-160 chars).",
            "seo_impact": "Increases search result real estate and click likelihood."
        })
    elif len(meta) > 160:
        structured_issues.append({
            "title": "Meta Description Too Long",
            "severity": "Low",
            "why_it_matters": "Long descriptions get truncated in search results, potentially cutting off your main call-to-action.",
            "recommended_fix": "Keep the description under 160 characters to ensure the whole message is visible.",
            "seo_impact": "Improves messaging clarity in search results."
        })
    
    # H1 check
    h1_c = h1_count if h1_count is not None else 0
    if h1_c == 0:
        structured_issues.append({
            "title": "Missing H1 Tag",
            "severity": "High",
            "why_it_matters": "Search engines use H1 tags to understand the primary topic of a page.",
            "recommended_fix": "Add exactly one descriptive H1 tag containing the main target keyword near the top of the page.",
            "seo_impact": "Improves content relevance, keyword targeting, and search engine understanding."
        })
    elif h1_c > 1:
        structured_issues.append({
            "title": f"Multiple H1 Tags ({h1_c})",
            "severity": "Medium",
            "why_it_matters": "Using multiple H1s can confuse search engines about the primary topic of the page.",
            "recommended_fix": "Keep exactly one H1 tag per page. Change the other H1s to H2s or H3s.",
            "seo_impact": "Clarifies topical focus for better rankings."
        })
    
    # Word count check
    wc = word_count if word_count is not None else 0
    if wc < 100:
        structured_issues.append({
            "title": f"Low Word Count ({wc} words)",
            "severity": "Medium",
            "why_it_matters": "Pages with very little content often struggle to rank because search engines have insufficient information about the topic.",
            "recommended_fix": "Increase the word count to at least 300+ words by adding more valuable, detailed information for users.",
            "seo_impact": "Boosts topical authority and chances to rank for related long-tail keywords."
        })
    
    # Indexing status check
    if not is_indexable:
        structured_issues.append({
            "title": "Page is Blocked from Indexing",
            "severity": "High",
            "why_it_matters": "This page has a 'noindex' tag, meaning search engines will intentionally ignore it.",
            "recommended_fix": "If this page SHOULD be in Google, remove the 'noindex' directive from the meta robots tag or headers.",
            "seo_impact": "Required for the page to receive any organic traffic."
        })

    # Parse incoming string issues from the backend
    page_issues = page.get("issues", {})
    issues_list = []
    if isinstance(page_issues, dict):
        issues_list = page_issues.get("critical", []) + page_issues.get("high", []) + page_issues.get("medium", []) + page_issues.get("low", [])
    elif isinstance(page_issues, list):
        issues_list = page_issues

    for raw_iss in issues_list:
        if isinstance(raw_iss, dict) and "title" in raw_iss:
            structured_issues.append(raw_iss)
        elif isinstance(raw_iss, str) and raw_iss:
            lower_iss = raw_iss.lower()
            if not any(k in lower_iss for k in ["title", "meta", "h1", "word count", "noindex"]):
                structured_issues.append({
                    "title": raw_iss,
                    "severity": "Medium",
                    "why_it_matters": "This issue was detected during the page audit and may affect SEO performance.",
                    "recommended_fix": "Review the specific finding and apply standard SEO best practices to resolve it.",
                    "seo_impact": "Fixing this improves overall page health and compliance."
                })

    # ── Recommendations ──────────────────────────────────────────────────────
    structured_recs = []
    for issue in structured_issues:
        structured_recs.append({
            "priority": issue["severity"],
            "issue": issue["title"],
            "recommendation": issue["recommended_fix"],
            "benefit": issue["seo_impact"]
        })

    return {
        "url": url,
        "title_length": title_length,
        "meta_description_length": meta_len,
        "word_count": word_count,
        "h1_count": h1_count,
        "headings": headings_obj,
        "is_indexable": is_indexable,
        "indexing_status": indexing_status,
        "seo_health": seo_health,
        # Pass through issues and recommendations
        "issues": structured_issues,
        "recommendations": structured_recs,
        # Pass through any extra fields that future frontend versions may use
        "page_info": page.get("page_info", {}),
        "canonical_url": page.get("page_info", {}).get("canonical") or page.get("canonical_url"),
        # Ensure deep tabs like Performance and Technical SEO get their data
        "performance": page.get("performance", {}),
        "technical_seo": page.get("technical_seo", {}),
        "content": page.get("content", {})
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

