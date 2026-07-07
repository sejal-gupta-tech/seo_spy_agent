from typing import Dict, Any

def calculate_consistency_score(public_audit_result: Dict[str, Any], gbp_profile: Dict[str, Any]) -> float:
    """
    Compares Website NAP vs GBP Profile NAP.
    """
    score = 100.0
    
    # Check Phone
    gbp_phone = gbp_profile.get("phoneNumbers", {}).get("primaryPhone", "")
    website_phones = public_audit_result.get("nap_analysis", {}).get("phones_found", [])
    
    # Very rudimentary phone matching (strip non-digits)
    def clean_phone(p):
        return ''.join(filter(str.isdigit, p))
    
    gbp_phone_clean = clean_phone(gbp_phone)
    if gbp_phone_clean:
        website_phones_clean = [clean_phone(p) for p in website_phones]
        
        # If GBP has a phone but website doesn't show it
        if gbp_phone_clean not in website_phones_clean:
            score -= 30.0
            
    # Check Domain
    gbp_domain = gbp_profile.get("websiteUri", "").replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
    website_domain = public_audit_result.get("website", "").replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
    
    if gbp_domain and website_domain:
        if not website_domain.startswith(gbp_domain) and not gbp_domain.startswith(website_domain):
            score -= 40.0
            
    return max(0.0, score)
