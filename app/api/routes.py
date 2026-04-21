from fastapi import APIRouter, HTTPException

from app.models.schema import FinalResponse, URLRequest, FixRequest, FixResponse
from app.services.scraper import analyze_url
from app.services.fix_generator import generate_fix
from app.utils.validators import is_valid_url, normalize_url

router = APIRouter()


@router.post("/generate-fix", response_model=FixResponse)
async def fix_issue(data: FixRequest):
    result = await generate_fix(data.issue)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.post("/analyze-url", response_model=FinalResponse)
async def analyze(data: URLRequest):
    normalized_url = normalize_url(data.url)

    if not is_valid_url(normalized_url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    result = await analyze_url(normalized_url)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


from fastapi.responses import FileResponse
import os

@router.get("/download-report/{task_id}")
def download_report(task_id: str):
    pdf_path = f"reports/{task_id}.pdf"
    html_path = f"reports/{task_id}.html"

    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf", filename="seo_report.pdf")

    elif os.path.exists(html_path):
        return FileResponse(html_path, media_type="text/html", filename="seo_report.html")

    return {"error": "Report not found"}
