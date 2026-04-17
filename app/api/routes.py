from fastapi import APIRouter, HTTPException

from app.models.schema import FinalResponse, URLRequest
from app.services.scraper import analyze_url
from app.utils.validators import is_valid_url, normalize_url

router = APIRouter()


@router.post("/analyze-url", response_model=FinalResponse)
async def analyze(data: URLRequest):
    normalized_url = normalize_url(data.url)

    if not is_valid_url(normalized_url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    result = await analyze_url(normalized_url)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result
