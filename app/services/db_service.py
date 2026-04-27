from datetime import datetime
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
        # Extract numeric SEO health score if possible (e.g. "85%" -> 85)
        raw_score = result.get("technical_audit", {}).get("overall_seo_health", "0")
        try:
            seo_score = int(str(raw_score).replace("%", ""))
        except ValueError:
            seo_score = 0

        project_doc = {
            "url": url,
            "business_type": business_type,
            "seo_score": seo_score,
            "report_url": result.get("report_url"),
            "created_at": datetime.utcnow()
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
            "data_limitations": result.get("data_limitations", [])
        }
        await db.ai_insights.insert_one(insights_doc)

        # 4. Prepare 'seo_data' (Keywords + Competitors)
        seo_data_doc = {
            "project_id": project_id,
            "competitive_intelligence": result.get("competitive_intelligence", {})
        }
        await db.seo_data.insert_one(seo_data_doc)

        # 5. Prepare 'crawl_data' (Page-level info)
        crawl_overview = result.get("crawl_overview", {})
        
        # Map sampled pages to the requested structure
        sampled_pages = []
        for p in crawl_overview.get("sampled_pages", []):
            sampled_pages.append({
                "url": p.get("url"),
                "seo_health": p.get("seo_health"),
                "canonical_url": p.get("canonical_url"),
                "dofollow_links": p.get("internal_links", {}).get("dofollow", 0),
                "nofollow_links": p.get("internal_links", {}).get("nofollow", 0),
                "key_issue": p.get("critical_issue", "None")
            })

        crawl_doc = {
            "project_id": project_id,
            "crawl_overview": {
                "analyzed_pages": crawl_overview.get("analyzed_pages", 0),
                "discovered_internal_pages": crawl_overview.get("discovered_internal_pages", 0),
                "coverage_ratio": crawl_overview.get("sample_coverage_ratio", "0%")
            },
            "pages": sampled_pages
        }
        await db.crawl_data.insert_one(crawl_doc)

        logger.info(f"Successfully saved all audit components for project {project_id}")
        return project_id

    except Exception as e:
        logger.error(f"Error saving split audit data: {e}")
        raise e


async def get_all_projects():
    """
    Returns a list of all analyzed projects.
    """
    db = db_manager.database
    if db is None:
        return []
    
    cursor = db.projects.find().sort("created_at", -1)
    projects = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        projects.append(doc)
    return projects

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

        audit_results = await db.audit_results.find_one({"project_id": project_id})
        ai_insights = await db.ai_insights.find_one({"project_id": project_id})
        seo_data = await db.seo_data.find_one({"project_id": project_id})
        crawl_data = await db.crawl_data.find_one({"project_id": project_id})

        # Reconstruct the FinalResponse structure
        # Note: We need to be careful with the mapping as save_audit_report slightly transformed some fields
        result = {
            "executive_summary": ai_insights.get("executive_summary", ""),
            "management_summary": ai_insights.get("management_summary", {}),
            "recommended_roadmap": ai_insights.get("recommended_roadmap", []),
            "data_limitations": ai_insights.get("data_limitations", []),
            "technical_audit": {
                "overall_seo_health": audit_results.get("overall_seo_health", 0),
                "metric_summary": audit_results.get("metric_summary", []),
                "findings": audit_results.get("findings", [])
            },
            "competitive_intelligence": seo_data.get("competitive_intelligence", {}),
            "crawl_overview": {
                "analyzed_pages": crawl_data.get("crawl_overview", {}).get("analyzed_pages", 0),
                "discovered_internal_pages": crawl_data.get("crawl_overview", {}).get("discovered_internal_pages", 0),
                "sample_coverage_ratio": crawl_data.get("crawl_overview", {}).get("coverage_ratio", "0%"),
                "sampled_pages": crawl_data.get("pages", []) # Map back 'pages' to 'sampled_pages'
            },
            "report_url": project.get("report_url")
        }

        # Since we might have lost some minor fields during the split-save, 
        # we check if those objects exist or need default nesting
        # The frontend mostly uses technical_audit, competitive_intelligence, management_summary, recommended_roadmap
        
        return result

    except Exception as e:
        logger.error(f"Error retrieving audit data for {project_id_str}: {e}")
        return None
