from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from app.core.config import REPORTS_DIR
from app.core.errors import ServiceError
from app.models.schema import (
    AnalysisJobAccepted,
    AnalysisJobStatus,
    FinalResponse,
    URLRequest,
    FixRequest,
    FixResponse,
)
from app.services.analysis_jobs import create_analysis_job, get_analysis_job
from app.services.analysis_stream import stream_analysis
from app.services.scraper import analyze_url
from app.services.fix_generator import generate_fix
from app.utils.validators import is_valid_url, normalize_url

router = APIRouter()


@router.post("/generate-fix", response_model=FixResponse)
async def fix_issue(data: FixRequest):
    try:
        return await generate_fix(data.issue)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/analyze-url", response_model=FinalResponse)
async def analyze(data: URLRequest):
    normalized_url = normalize_url(data.url)

    if not is_valid_url(normalized_url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    result = await analyze_url(normalized_url)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/analysis-jobs", response_model=AnalysisJobAccepted, status_code=202)
async def submit_analysis_job(data: URLRequest):
    normalized_url = normalize_url(data.url)

    if not is_valid_url(normalized_url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    return await create_analysis_job(normalized_url)


@router.get("/analysis-jobs/{job_id}", response_model=AnalysisJobStatus)
async def read_analysis_job(job_id: str):
    job = await get_analysis_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    return job


@router.post("/analyze-url/stream")
async def analyze_stream(data: URLRequest):
    normalized_url = normalize_url(data.url)

    if not is_valid_url(normalized_url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    return StreamingResponse(
        stream_analysis(normalized_url),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/download-report/{task_id}")
def download_report(task_id: str):
    pdf_path = REPORTS_DIR / f"{task_id}.pdf"
    html_path = REPORTS_DIR / f"{task_id}.html"

    if pdf_path.exists():
        return FileResponse(str(pdf_path), media_type="application/pdf", filename="seo_report.pdf")

    if html_path.exists():
        return FileResponse(str(html_path), media_type="text/html", filename="seo_report.html")

    raise HTTPException(status_code=404, detail="Report not found")
