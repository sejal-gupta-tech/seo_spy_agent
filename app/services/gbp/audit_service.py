import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from app.models.schema import GBPAuditResponse
from app.services.gbp.profile_service import fetch_mock_profile

async def run_gbp_profile_audit(user_id: str, location_reference: str) -> GBPAuditResponse:
    profile = await fetch_mock_profile(location_reference)
    
    issues = []
    recommendations = []
    scores = {}
    
    # 1. Profile Completeness
    completeness = 0
    if profile.get("profile", {}).get("description"):
        completeness += 25
    else:
        issues.append({
            "issue": "Missing Business Description",
            "priority": "High",
            "explanation": "A detailed description helps customers and search engines understand your business.",
            "recommendation": "Add a 750-character SEO-optimized description to your profile."
        })
        
    if profile.get("regularHours"):
        completeness += 25
    else:
        issues.append({
            "issue": "Missing Business Hours",
            "priority": "High",
            "explanation": "Customers need to know when you are open.",
            "recommendation": "Add accurate regular business hours."
        })
        
    if profile.get("phoneNumbers", {}).get("primaryPhone"):
        completeness += 25
    if profile.get("websiteUri"):
        completeness += 25
        
    scores["completeness_score"] = completeness
    
    # 2. Category Optimization
    category_score = 0
    if profile.get("primaryCategory"):
        category_score += 50
    if profile.get("additionalCategories") and len(profile.get("additionalCategories")) > 0:
        category_score += 50
    else:
        issues.append({
            "issue": "No Secondary Categories",
            "priority": "Medium",
            "explanation": "Secondary categories help your business show up for a wider variety of local searches.",
            "recommendation": "Add 2-3 relevant secondary categories."
        })
        
    scores["category_optimization_score"] = category_score
    
    # 3. Media & Engagement (Mocked)
    scores["media_engagement_score"] = 60
    
    # Overall Score
    scores["overall_gbp_score"] = round((completeness + category_score + scores["media_engagement_score"]) / 3, 1)
    
    if scores["overall_gbp_score"] > 80:
        recommendations.append({
            "issue": "Strong GBP Profile",
            "priority": "Low",
            "explanation": "Your Google Business Profile is well-optimized.",
            "recommendation": "Continue adding weekly updates and collecting positive reviews."
        })

    return GBPAuditResponse(
        audit_id=str(uuid.uuid4()),
        user_id=user_id,
        website_url=profile.get("websiteUri"),
        selected_location_reference=location_reference,
        scores=scores,
        issues=issues,
        recommendations=recommendations,
        created_at=datetime.now(timezone.utc).isoformat()
    )
