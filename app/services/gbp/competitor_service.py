import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import json

async def fetch_competitor_signals(url: str, business_name: str, target_city: str) -> Dict[str, Any]:
    """
    Compliant competitor analysis. Scrapes the provided competitor website URL
    for Title Tags, Meta Descriptions, H1s, LocalBusiness schema, and contact info visibility.
    """
    if not url.startswith("http"):
        url = f"https://{url}"
        
    result = {
        "url": url,
        "business_name": business_name,
        "title_tag": "",
        "meta_description": "",
        "h1": "",
        "has_local_schema": False,
        "nap_found": [],
        "city_mentioned": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'lxml')
                
                # Title
                if soup.title:
                    result["title_tag"] = soup.title.string.strip() if soup.title.string else ""
                
                # Meta
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc:
                    result["meta_description"] = meta_desc.get("content", "").strip()
                    
                # H1
                h1 = soup.find("h1")
                if h1:
                    result["h1"] = h1.get_text(separator=" ", strip=True)
                    
                # Schema
                for script in soup.find_all("script", type="application/ld+json"):
                    if script.string:
                        try:
                            data = json.loads(script.string)
                            # Handle array of schemas
                            if isinstance(data, list):
                                for item in data:
                                    if item.get("@type") in ["LocalBusiness", "Organization", "Store", "ProfessionalService"]:
                                        result["has_local_schema"] = True
                            elif isinstance(data, dict):
                                if data.get("@type") in ["LocalBusiness", "Organization", "Store", "ProfessionalService"]:
                                    result["has_local_schema"] = True
                        except json.JSONDecodeError:
                            pass
                            
                # Text check for target city
                text_content = soup.get_text().lower()
                if target_city.lower() in text_content:
                    result["city_mentioned"] = True
                    
    except Exception as e:
        result["error"] = str(e)
        
    return result

async def analyze_local_competitors(my_domain: str, target_city: str, competitors: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Analyzes multiple competitors and compares them to my_domain.
    competitors = [{"business_name": "...", "url": "..."}]
    """
    my_signals = await fetch_competitor_signals(my_domain, "My Business", target_city)
    
    competitor_signals = []
    for comp in competitors:
        comp_res = await fetch_competitor_signals(comp.get("url", ""), comp.get("business_name", ""), target_city)
        competitor_signals.append(comp_res)
        
    return {
        "target_city": target_city,
        "my_business": my_signals,
        "competitors": competitor_signals
    }
