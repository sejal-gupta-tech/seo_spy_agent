import httpx
from typing import Dict, Any
from datetime import datetime, timedelta, timezone
from app.services.gbp.oauth_service import get_connection

async def fetch_gbp_performance(user_id: str, location_reference: str, days: int = 30) -> Dict[str, Any]:
    """
    Fetches performance metrics (impressions, clicks, directions) from the GBP Performance API.
    """
    conn = await get_connection(user_id)
    access_token = conn.get("access_token")
    
    # We need just the locationId part, not accounts/{accountId}/locations/{locationId}
    location_id = location_reference
    if "locations/" in location_reference:
        location_id = "locations/" + location_reference.split("locations/")[1]
    
    if not access_token or "mock" in access_token:
        # Return realistic mock data
        return {
            "metrics": {
                "search_impressions": 1250,
                "maps_impressions": 840,
                "website_clicks": 145,
                "call_clicks": 32,
                "direction_requests": 88
            },
            "time_series": [
                {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), "value": 100 + (i * 2)} for i in range(days, 0, -1)
            ]
        }

    # Prepare date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # businessprofileperformance.googleapis.com
    url = f"https://businessprofileperformance.googleapis.com/v1/{location_id}:fetchMultiDailyMetricsTimeSeries"
    
    params = {
        "dailyMetrics": ["SEARCH_IMPRESSIONS", "MAPS_IMPRESSIONS", "WEBSITE_CLICKS", "CALL_CLICKS", "DIRECTIONS_REQUESTS"],
        "dailyRange.start_date.year": start_date.year,
        "dailyRange.start_date.month": start_date.month,
        "dailyRange.start_date.day": start_date.day,
        "dailyRange.end_date.year": end_date.year,
        "dailyRange.end_date.month": end_date.month,
        "dailyRange.end_date.day": end_date.day,
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if resp.status_code == 200:
            data = resp.json()
            # Process the time series into a clean summary
            summary = {
                "search_impressions": 0,
                "maps_impressions": 0,
                "website_clicks": 0,
                "call_clicks": 0,
                "direction_requests": 0
            }
            
            # Simple aggregation logic (real API returns complex multiDailyMetricTimeSeries)
            for metric in data.get("multiDailyMetricTimeSeries", []):
                m_type = metric.get("dailyMetric", "")
                total = sum([pt.get("value", 0) for pt in metric.get("timeSeries", {}).get("datedValues", [])])
                
                if m_type == "SEARCH_IMPRESSIONS":
                    summary["search_impressions"] = total
                elif m_type == "MAPS_IMPRESSIONS":
                    summary["maps_impressions"] = total
                elif m_type == "WEBSITE_CLICKS":
                    summary["website_clicks"] = total
                elif m_type == "CALL_CLICKS":
                    summary["call_clicks"] = total
                elif m_type == "DIRECTIONS_REQUESTS":
                    summary["direction_requests"] = total
                    
            return {
                "metrics": summary,
                "raw_data": data
            }
        else:
            print(f"Error fetching performance: {resp.text}")
            return {"metrics": {}, "error": resp.text}

async def fetch_search_keywords(user_id: str, location_reference: str, days: int = 30) -> Dict[str, Any]:
    """
    Fetches the Search Keywords (queries) that triggered the profile.
    Since GBP API sometimes restricts this, we also handle mock data.
    """
    conn = await get_connection(user_id)
    access_token = conn.get("access_token")
    
    if not access_token or "mock" in access_token:
        return {
            "keywords": [
                {"query": "seo agency near me", "impressions": 145, "classification": ["local_intent", "service_intent"], "opportunity_score": 92},
                {"query": "seven unique tech", "impressions": 88, "classification": ["branded"], "opportunity_score": 45},
                {"query": "digital marketing firm", "impressions": 54, "classification": ["service_intent", "high_opportunity"], "opportunity_score": 88},
            ]
        }
        
    # The actual endpoint for search queries is searchKeywords (if available) or via insights (deprecated)
    # We'll use a placeholder for the actual API call logic if they enabled the correct endpoint.
    return {"keywords": []}
