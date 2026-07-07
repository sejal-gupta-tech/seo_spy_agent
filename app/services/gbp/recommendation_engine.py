import uuid
from typing import Dict, Any, List

def calculate_combined_health_score(
    website_score: float,
    gbp_score: float,
    review_score: float,
    performance_score: float
) -> float:
    """
    Calculates a weighted overall Local SEO Health Score.
    Weights: Website (30%), GBP Profile (30%), Reviews (25%), Performance (15%)
    """
    score = (
        (website_score * 0.30) +
        (gbp_score * 0.30) +
        (review_score * 0.25) +
        (performance_score * 0.15)
    )
    return round(score, 1)

def generate_local_seo_recommendations(
    website_audit: Dict[str, Any],
    public_local_audit: Dict[str, Any],
    gbp_audit: Dict[str, Any],
    review_summary: Dict[str, Any],
    performance: Dict[str, Any],
    keywords: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Synthesizes data from various modules to generate actionable AI recommendations.
    """
    recs = []
    
    # Check GBP Audit
    if gbp_audit:
        issues = gbp_audit.get("issues", [])
        for issue in issues:
            recs.append({
                "recommendation_id": str(uuid.uuid4()),
                "priority": issue.get("priority", "Medium"),
                "category": "GBP Optimization",
                "title": issue.get("issue"),
                "why_it_matters": issue.get("explanation"),
                "recommended_action": issue.get("recommendation"),
                "expected_impact": "High" if issue.get("priority") == "High" else "Medium",
                "effort": "Low",
                "source_modules": ["GBP Profile"]
            })
            
    # Check Reviews
    if review_summary:
        response_rate = review_summary.get("summary", {}).get("response_rate", 100)
        unreplied = review_summary.get("summary", {}).get("unreplied_count", 0)
        if response_rate < 80 and unreplied > 0:
            recs.append({
                "recommendation_id": str(uuid.uuid4()),
                "priority": "High",
                "category": "Reputation Management",
                "title": "Low Review Response Rate",
                "why_it_matters": f"You have {unreplied} unreplied reviews. Responding to reviews builds trust and improves local ranking.",
                "recommended_action": "Use the AI Reply Generator to catch up on unreplied reviews.",
                "expected_impact": "High",
                "effort": "Medium",
                "source_modules": ["Review Intelligence"]
            })
            
    # Check Public Local Audit
    if public_local_audit:
        scores = public_local_audit.get("scores", {})
        if scores.get("schema_score", 100) < 50:
            recs.append({
                "recommendation_id": str(uuid.uuid4()),
                "priority": "Critical",
                "category": "Website Local SEO",
                "title": "Missing LocalBusiness Schema",
                "why_it_matters": "Structured data helps Google understand your business entity explicitly.",
                "recommended_action": "Add valid LocalBusiness JSON-LD schema to your homepage and location pages.",
                "expected_impact": "High",
                "effort": "Low",
                "source_modules": ["Public Local Audit"]
            })
            
    # Add an AI-driven placeholder for the opportunity logic based on keywords
    if keywords and keywords.get("keywords"):
        top_keyword = sorted(keywords["keywords"], key=lambda k: k.get("opportunity_score", 0), reverse=True)
        if top_keyword:
            kw = top_keyword[0]
            recs.append({
                "recommendation_id": str(uuid.uuid4()),
                "priority": "Medium",
                "category": "Keyword Opportunity",
                "title": f"Target Keyword: {kw.get('query')}",
                "why_it_matters": f"This term received {kw.get('impressions')} impressions but lacks strong website relevance.",
                "recommended_action": f"Create a dedicated service page or optimize existing H1s for '{kw.get('query')}'.",
                "expected_impact": "High",
                "effort": "High",
                "source_modules": ["Search Keyword Intelligence", "Website Audit"]
            })
            
    return recs
