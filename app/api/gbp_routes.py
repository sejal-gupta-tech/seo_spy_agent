import logging
import traceback
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Security
from pydantic import BaseModel

from app.api.routes import _require_api_key
from app.core.logger import logger

from app.models.schema import PublicLocalAuditRequest, LocalSeoAuditResponse
from app.services.gbp.public_audit import run_public_local_audit

gbp_router = APIRouter(prefix="/gbp", tags=["Local SEO & GBP"])

@gbp_router.get("/")
async def gbp_root():
    return {"status": "ok", "message": "GBP API is online"}

@gbp_router.post("/public-audit", response_model=LocalSeoAuditResponse)
async def public_local_audit(request: PublicLocalAuditRequest):
    """
    Runs a public local SEO audit (NAP, Schema, Location pages) without requiring Google authentication.
    """
    try:
        result = await run_public_local_audit(request)
        return result
    except Exception as e:
        logger.error(f"Error in public_local_audit: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

class OAuthStartRequest(BaseModel):
    redirect_uri: str

class OAuthCallbackRequest(BaseModel):
    code: str
    redirect_uri: str
    
class SelectLocationRequest(BaseModel):
    user_id: str
    account_name: str
    location_name: str

from app.services.gbp.oauth_service import start_oauth_flow, process_oauth_callback, get_connection, update_selected_location
from app.services.gbp.account_service import list_mock_accounts, list_mock_locations

@gbp_router.post("/auth/start")
async def gbp_auth_start(req: OAuthStartRequest):
    """
    Returns the Google OAuth login URL.
    """
    url = await start_oauth_flow(req.redirect_uri)
    return {"auth_url": url}

@gbp_router.post("/auth/callback")
async def gbp_auth_callback(req: OAuthCallbackRequest):
    """
    Exchanges the OAuth code for tokens and returns a user_session_id.
    """
    user_id = await process_oauth_callback(req.code, req.redirect_uri)
    return {"user_id": user_id, "status": "connected"}

@gbp_router.get("/accounts")
async def get_gbp_accounts(user_id: str):
    """
    Returns the GBP accounts the user has access to.
    """
    conn = await get_connection(user_id)
    if not conn:
        raise HTTPException(status_code=401, detail="User not authenticated with Google")
    
    accounts = await list_mock_accounts(user_id)
    return {"accounts": accounts}

@gbp_router.get("/accounts/{account_id}/locations")
async def get_gbp_locations(user_id: str, account_id: str):
    """
    Returns locations under a specific account.
    """
    full_account_name = f"accounts/{account_id}"
    locations = await list_mock_locations(user_id, full_account_name)
    return {"locations": locations}

@gbp_router.post("/select-location")
async def select_gbp_location(req: SelectLocationRequest):
    """
    Saves the user's selected location to their connection record.
    """
    success = await update_selected_location(req.user_id, req.account_name, req.location_name)
    return {"success": success}

from app.models.schema import GBPAuditResponse
from app.services.gbp.audit_service import run_gbp_profile_audit

@gbp_router.get("/profile-audit", response_model=GBPAuditResponse)
async def get_gbp_profile_audit(user_id: str, location_reference: str):
    """
    Runs an audit on the selected Google Business Profile location.
    """
    try:
        # Reconstruct properly if passed weirdly, but usually client sends it correctly encoded
        result = await run_gbp_profile_audit(user_id, location_reference)
        return result
    except Exception as e:
        logger.error(f"Error in get_gbp_profile_audit: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

from app.services.gbp.review_service import fetch_gbp_reviews, analyze_review_intelligence, generate_ai_reply

class GenerateReplyRequest(BaseModel):
    review_text: str
    rating: int
    business_name: str = "Our Business"

@gbp_router.get("/reviews")
async def get_reviews(user_id: str, location_reference: str, page_token: str = ""):
    """
    Fetches authorized review data for the selected GBP location.
    """
    try:
        data = await fetch_gbp_reviews(user_id, location_reference, page_token)
        return data
    except Exception as e:
        logger.error(f"Error in get_reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@gbp_router.get("/reviews/summary")
async def get_reviews_summary(user_id: str, location_reference: str):
    """
    Returns AI/NLP analysis of reviews.
    """
    try:
        data = await fetch_gbp_reviews(user_id, location_reference)
        reviews = data.get("reviews", [])
        summary = analyze_review_intelligence(reviews)
        return summary
    except Exception as e:
        logger.error(f"Error in get_reviews_summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@gbp_router.post("/reviews/{review_id}/generate-reply")
async def ai_generate_reply(review_id: str, req: GenerateReplyRequest):
    """
    Uses OpenAI to generate a suggested owner reply.
    """
    reply = await generate_ai_reply(req.review_text, req.rating, req.business_name)
    return {"suggested_reply": reply}

from app.services.gbp.performance_service import fetch_gbp_performance, fetch_search_keywords

@gbp_router.get("/performance/summary")
async def get_performance_summary(user_id: str, location_reference: str, days: int = 30):
    """
    Returns official Business Profile Performance metrics (impressions, clicks).
    """
    try:
        data = await fetch_gbp_performance(user_id, location_reference, days)
        return data
    except Exception as e:
        logger.error(f"Error in get_performance_summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@gbp_router.get("/search-keywords")
async def get_search_keywords(user_id: str, location_reference: str, days: int = 30):
    """
    Returns search keywords data and local opportunity score.
    """
    try:
        data = await fetch_search_keywords(user_id, location_reference, days)
        return data
    except Exception as e:
        logger.error(f"Error in get_search_keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from app.services.gbp.rag_service import ask_rag_question

class RagRequest(BaseModel):
    question: str

@gbp_router.post("/ask")
async def ask_local_seo_rag(user_id: str, location_reference: str, req: RagRequest):
    """
    Queries the ChromaDB Vector store to answer questions about this specific local SEO profile.
    """
    try:
        response = await ask_rag_question(user_id, location_reference, req.question)
        return response
    except Exception as e:
        logger.error(f"Error in RAG endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from app.services.gbp.recommendation_engine import calculate_combined_health_score, generate_local_seo_recommendations
from app.services.db_service import save_gbp_snapshot, get_gbp_snapshots

class DashboardSummaryRequest(BaseModel):
    user_id: str
    location_reference: str
    public_audit_data: Dict[str, Any]
    gbp_audit_data: Dict[str, Any]
    reviews_data: Dict[str, Any]
    performance_data: Dict[str, Any]
    keywords_data: Dict[str, Any]

@gbp_router.post("/dashboard/summary")
async def get_dashboard_summary(req: DashboardSummaryRequest):
    """
    Combines data from all sources to generate the Combined SEO Health Score 
    and AI Recommendations, and saves a historical snapshot.
    """
    try:
        # Extract individual scores
        website_score = req.public_audit_data.get("scores", {}).get("overall_local_score", 0)
        gbp_score = req.gbp_audit_data.get("scores", {}).get("overall_score", 0)
        review_score = req.reviews_data.get("summary", {}).get("response_rate", 0) # Simplification
        
        # Calculate combined health score
        combined_score = calculate_combined_health_score(
            website_score=float(website_score),
            gbp_score=float(gbp_score),
            review_score=float(review_score),
            performance_score=100.0 # Placeholder for performance score
        )
        
        # Generate recommendations
        recommendations = generate_local_seo_recommendations(
            website_audit=req.public_audit_data,
            public_local_audit=req.public_audit_data,
            gbp_audit=req.gbp_audit_data,
            review_summary=req.reviews_data,
            performance=req.performance_data,
            keywords=req.keywords_data
        )
        
        # Save historical snapshot asynchronously (or synchronously for now)
        snapshot_metrics = {
            "website_score": website_score,
            "gbp_score": gbp_score,
            "review_score": review_score,
        }
        await save_gbp_snapshot(req.user_id, req.location_reference, combined_score, snapshot_metrics)
        
        return {
            "combined_health_score": combined_score,
            "recommendations": recommendations,
            "snapshot_saved": True
        }
    except Exception as e:
        logger.error(f"Error in dashboard/summary: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@gbp_router.get("/dashboard/snapshots")
async def get_historical_snapshots(user_id: str, location_reference: str, limit: int = 12):
    """
    Retrieves historical GBP snapshots for charting.
    """
    try:
        snapshots = await get_gbp_snapshots(user_id, location_reference, limit)
        return {"snapshots": snapshots}
    except Exception as e:
        logger.error(f"Error in dashboard/snapshots: {e}")
        raise HTTPException(status_code=500, detail=str(e))
