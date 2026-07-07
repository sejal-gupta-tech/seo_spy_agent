import re
from typing import Any, Dict, List
import httpx
from bs4 import BeautifulSoup
import json
import uuid
import datetime

from app.models.schema import PublicLocalAuditRequest, LocalSeoAuditResponse, LocalLocation, LocalScores

async def run_public_local_audit(request: PublicLocalAuditRequest) -> LocalSeoAuditResponse:
    url = request.url if request.url.startswith("http") else f"https://{request.url}"
    
    # 1. Fetch the page
    html = ""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        # If we can't fetch, return a basic response with 0 scores and an issue
        scores = LocalScores(local_seo_score=0, nap_score=0, schema_score=0, location_page_score=0, local_onpage_score=0, local_technical_score=0)
        return LocalSeoAuditResponse(
            audit_id=str(uuid.uuid4()),
            website=url,
            business_name=request.business_name,
            target_location=LocalLocation(city=request.target_city, country=request.target_country),
            scores=scores,
            issues=[{"issue": "Failed to fetch URL", "detail": str(e), "priority": "High"}]
        )

    soup = BeautifulSoup(html, "html.parser")
    
    # 2. Extract NAP (Name, Address, Phone) roughly
    text = soup.get_text(separator=" ", strip=True)
    
    # Simple regex for phone numbers (US format approx)
    phone_matches = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    phone_numbers = list(set(phone_matches))
    
    # Check for address-like structures or specific city
    address_found = False
    if request.target_city and request.target_city.lower() in text.lower():
        address_found = True
        
    nap_score = 0
    if len(phone_numbers) > 0:
        nap_score += 50
    if address_found:
        nap_score += 50
        
    nap_analysis = {
        "phones_found": phone_numbers,
        "target_city_mentioned": address_found,
        "is_complete": nap_score == 100
    }
    
    # 3. Check for LocalBusiness Schema
    schemas_found = []
    has_local_business = False
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                schemas_found.append(data.get("@type"))
                if data.get("@type") == "LocalBusiness" or data.get("@type") in ["Organization", "Store", "Restaurant"]:
                    has_local_business = True
            elif isinstance(data, list):
                for item in data:
                    schemas_found.append(item.get("@type"))
                    if item.get("@type") == "LocalBusiness" or item.get("@type") in ["Organization", "Store", "Restaurant"]:
                        has_local_business = True
        except Exception:
            pass
            
    schema_score = 100 if has_local_business else 0
    schema_analysis = {
        "schemas_detected": list(set([s for s in schemas_found if s])),
        "has_local_business_schema": has_local_business
    }
    
    # 4. Check for Location / Contact Pages
    links = soup.find_all("a", href=True)
    location_pages = []
    for a in links:
        href = a['href'].lower()
        if "contact" in href or "location" in href or "about" in href:
            location_pages.append({"text": a.get_text(strip=True), "url": a['href']})
            
    location_page_score = 100 if len(location_pages) > 0 else 0
    contact_page_analysis = {
        "has_contact_page": len(location_pages) > 0,
        "location_pages_found": len(location_pages)
    }
    
    # 5. Compile Scores & Issues
    local_seo_score = (nap_score * 0.4) + (schema_score * 0.4) + (location_page_score * 0.2)
    scores = LocalScores(
        local_seo_score=round(local_seo_score, 1),
        nap_score=nap_score,
        schema_score=schema_score,
        location_page_score=location_page_score,
        local_onpage_score=0,
        local_technical_score=0
    )
    
    issues = []
    recommendations = []
    
    if not has_local_business:
        issues.append({
            "issue": "Missing LocalBusiness Schema",
            "priority": "High",
            "explanation": "Schema markup helps search engines understand your business details.",
            "recommendation": "Add application/ld+json LocalBusiness schema to your homepage and contact pages."
        })
    if nap_score < 100:
        issues.append({
            "issue": "Incomplete NAP Details",
            "priority": "Medium",
            "explanation": "Name, Address, and Phone number should be clearly visible in HTML text.",
            "recommendation": "Ensure your phone number and physical address (including city/state) are in the footer."
        })
        
    if scores.local_seo_score == 100:
        recommendations.append({
            "issue": "Excellent Local Baseline",
            "priority": "Low",
            "explanation": "Basic on-page local signals are present.",
            "recommendation": "Focus on Google Business Profile consistency and local citations."
        })

    return LocalSeoAuditResponse(
        audit_id=str(uuid.uuid4()),
        website=url,
        business_name=request.business_name,
        target_location=LocalLocation(city=request.target_city, country=request.target_country),
        scores=scores,
        nap_analysis=nap_analysis,
        schema_analysis=schema_analysis,
        contact_page_analysis=contact_page_analysis,
        location_pages=location_pages,
        issues=issues,
        recommendations=recommendations
    )
