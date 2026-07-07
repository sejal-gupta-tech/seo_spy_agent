from typing import Dict, Any

async def fetch_mock_profile(location_name: str) -> Dict[str, Any]:
    """
    Mocks fetching a location profile from GBP API.
    """
    if "9384759283" in location_name:
        return {
            "name": location_name,
            "title": "Seven Unique Tech Solutions - Main Office",
            "primaryCategory": {"displayName": "Software Company", "categoryId": "gcid:software_company"},
            "additionalCategories": [{"displayName": "IT Services"}],
            "phoneNumbers": {"primaryPhone": "(555) 123-4567"},
            "storeCode": "HQ-01",
            "regularHours": {
                "periods": [
                    {"openDay": "MONDAY", "openTime": "09:00", "closeDay": "MONDAY", "closeTime": "17:00"},
                    {"openDay": "TUESDAY", "openTime": "09:00", "closeDay": "TUESDAY", "closeTime": "17:00"},
                    {"openDay": "WEDNESDAY", "openTime": "09:00", "closeDay": "WEDNESDAY", "closeTime": "17:00"},
                    {"openDay": "THURSDAY", "openTime": "09:00", "closeDay": "THURSDAY", "closeTime": "17:00"},
                    {"openDay": "FRIDAY", "openTime": "09:00", "closeDay": "FRIDAY", "closeTime": "17:00"}
                ]
            },
            "profile": {
                "description": "We are a leading software company specializing in AI solutions and SEO tools."
            },
            "websiteUri": "https://www.sevenunique.com",
            "storefrontAddress": {
                "locality": "San Francisco",
                "regionCode": "US",
                "postalCode": "94105",
                "addressLines": ["123 Tech Lane", "Suite 400"]
            }
        }
    else:
        return {
            "name": location_name,
            "title": "Acme Marketing",
            "primaryCategory": {"displayName": "Marketing Agency"},
            "websiteUri": "https://www.acme.com",
            "storefrontAddress": {
                "locality": "New York",
                "addressLines": ["456 Madison Ave"]
            }
        }
