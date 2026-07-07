import httpx
from typing import List, Dict, Any
from app.services.gbp.oauth_service import get_connection

async def list_mock_accounts(user_id: str) -> List[Dict[str, Any]]:
    """
    Fetches Google Business Profile accounts associated with the user token.
    Uses the real Google My Business API if an access token is available.
    """
    conn = await get_connection(user_id)
    access_token = conn.get("access_token")
    
    if not access_token or "mock" in access_token:
        # Fallback to mock data for testing
        return [
            {
                "name": "accounts/1049283749283",
                "accountName": "Seven Unique Tech Solutions",
                "type": "PERSONAL",
                "verificationState": "VERIFIED"
            },
            {
                "name": "accounts/8237492837492",
                "accountName": "Acme Corp Agency",
                "type": "ORGANIZATION",
                "verificationState": "VERIFIED"
            }
        ]

    # Real API call
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://mybusinessaccountmanagement.googleapis.com/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("accounts", [])
        else:
            print(f"Error fetching accounts: {resp.text}")
            return []

async def list_mock_locations(user_id: str, account_name: str) -> List[Dict[str, Any]]:
    """
    Fetches Google Business Profile locations for a specific account.
    """
    conn = await get_connection(user_id)
    access_token = conn.get("access_token")
    
    if not access_token or "mock" in access_token:
        if "1049283749283" in account_name:
            return [
                {
                    "name": f"{account_name}/locations/9384759283",
                    "locationName": "Seven Unique Tech Solutions - Main Office",
                    "primaryCategory": {"displayName": "Software Company", "categoryId": "gcid:software_company"},
                    "address": {
                        "regionCode": "US",
                        "locality": "San Francisco",
                        "addressLines": ["123 Tech Lane"]
                    },
                    "storeCode": "HQ-01",
                    "phoneNumbers": {"primaryPhone": "(555) 123-4567"},
                    "websiteUrl": "https://www.sevenunique.com"
                }
            ]
        else:
            return [
                {
                    "name": f"{account_name}/locations/111222333",
                    "locationName": "Acme Marketing",
                    "primaryCategory": {"displayName": "Marketing Agency", "categoryId": "gcid:marketing_agency"},
                    "address": {
                        "regionCode": "US",
                        "locality": "New York",
                        "addressLines": ["456 Madison Ave"]
                    },
                    "websiteUrl": "https://www.acme.com"
                }
            ]

    # Real API call
    async with httpx.AsyncClient() as client:
        # Note: the readMask is required for v1/locations endpoint in GBP
        resp = await client.get(
            f"https://mybusinessbusinessinformation.googleapis.com/v1/{account_name}/locations?readMask=name,title,storefrontAddress,websiteUri,phoneNumbers,categories",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if resp.status_code == 200:
            data = resp.json()
            # Normalize to match expected fields in mock for frontend compatibility
            locations = []
            for loc in data.get("locations", []):
                locations.append({
                    "name": loc.get("name"),
                    "locationName": loc.get("title"),
                    "primaryCategory": loc.get("categories", {}).get("primaryCategory", {}),
                    "address": loc.get("storefrontAddress", {}),
                    "phoneNumbers": loc.get("phoneNumbers", {}),
                    "websiteUrl": loc.get("websiteUri")
                })
            return locations
        else:
            print(f"Error fetching locations: {resp.text}")
            return []
