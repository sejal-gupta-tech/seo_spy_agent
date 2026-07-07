import uuid
import httpx
from typing import Dict, Any
from datetime import datetime, timezone
import os

from app.models.schema import GBPConnection
from app.core.database import db_manager
from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from fastapi import HTTPException

# Scopes needed for GBP APIs
GBP_SCOPES = [
    "https://www.googleapis.com/auth/business.manage",
    "https://www.googleapis.com/auth/plus.business.manage"
]

async def start_oauth_flow(redirect_uri: str) -> str:
    """
    Returns the authorization URL for Google OAuth.
    """
    if not GOOGLE_CLIENT_ID:
        # Fallback to mock behavior if no client ID is set for local testing
        return f"https://mock-oauth.local/auth?redirect_uri={redirect_uri}"

    scopes = "%20".join(GBP_SCOPES)
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scopes}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    return auth_url

async def process_oauth_callback(code: str, redirect_uri: str) -> str:
    """
    Exchanges the auth code for a token and stores it in the DB.
    Returns a user_id/session_id to the frontend.
    """
    mock_user_id = f"usr_{uuid.uuid4().hex[:8]}"

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        # Mock connection if no real credentials
        access_token = f"ya29.mock_{uuid.uuid4().hex}"
        refresh_token = f"1//mock_{uuid.uuid4().hex}"
    else:
        # Real token exchange
        async with httpx.AsyncClient() as client:
            resp = await client.post("https://oauth2.googleapis.com/token", data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            })
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"OAuth token exchange failed: {resp.text}")
            
            token_data = resp.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token", "") # Might not be returned if not first authorization
            
    connection = {
        "user_id": mock_user_id,
        "provider": "google",
        "account_reference": None,
        "selected_location_reference": None,
        "scopes": GBP_SCOPES,
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "status": "connected",
        "access_token": access_token,
        "refresh_token": refresh_token
    }
    
    if db_manager.database is not None:
        await db_manager.database["gbp_connections"].insert_one(connection)
        
    return mock_user_id

async def get_connection(user_id: str) -> dict:
    if db_manager.database is not None:
        conn = await db_manager.database["gbp_connections"].find_one({"user_id": user_id})
        if conn:
            conn["_id"] = str(conn["_id"])
            return conn
    
    # Fallback for testing without DB
    return {
        "user_id": user_id,
        "status": "connected",
        "provider": "google",
        "access_token": "ya29.mock"
    }

async def update_selected_location(user_id: str, account_name: str, location_name: str) -> bool:
    if db_manager.database is not None:
        result = await db_manager.database["gbp_connections"].update_one(
            {"user_id": user_id},
            {"$set": {
                "account_reference": account_name,
                "selected_location_reference": location_name,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return result.modified_count > 0
    return True
