import os
import re
import traceback
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security.api_key import APIKeyHeader
from app.core.logger import logger
from app.core.errors import ServiceError
from app.core.config import REPORTS_DIR
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
from app.services.db_service import save_audit_report, get_all_projects, get_project_audit

router = APIRouter()

# ---------------------------------------------------------------------------
# Optional API key authentication
# Set SEO_SPY_API_KEY in your .env to enable key enforcement.
# If the env var is not set (or empty), auth is skipped — useful for local dev.
# ---------------------------------------------------------------------------
_API_KEY_ENV = os.getenv("SEO_SPY_API_KEY", "").strip()
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _require_api_key(key: str | None = Security(_api_key_header)) -> None:
    """Dependency that enforces the API key when SEO_SPY_API_KEY is configured."""
    if not _API_KEY_ENV:
        # No key configured → open access (dev mode)
        return
    if key != _API_KEY_ENV:
        raise HTTPException(status_code=403, detail="Invalid or missing API key.")


# ---------------------------------------------------------------------------
# Task-ID validation helper — prevents path traversal in /download-report
# ---------------------------------------------------------------------------
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _validate_task_id(task_id: str) -> str:
    """Raise 400 if task_id is not a valid UUID (prevents path traversal)."""
    if not _UUID_RE.match(task_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid report ID format.",
        )
    return task_id


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/generate-fix", response_model=FixResponse, dependencies=[Depends(_require_api_key)])
async def fix_issue(data: FixRequest):
    try:
        result = await generate_fix(data.issue)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unhandled error in /generate-fix: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Fix generation failed: {exc}")


@router.post("/analyze", response_model=FinalResponse, dependencies=[Depends(_require_api_key)])
@router.post("/analyze-url", response_model=FinalResponse, dependencies=[Depends(_require_api_key)])
async def analyze(data: URLRequest):
    normalized_url = normalize_url(data.url)

    if not is_valid_url(normalized_url):
        raise HTTPException(status_code=400, detail="Invalid URL.")

    try:
        result = await analyze_url(normalized_url)
        
        # Store in MongoDB via Service Layer (Multi-collection split)
        if isinstance(result, dict) and "error" not in result:
            try:
                await save_audit_report(normalized_url, data.business_type, result)
            except Exception as db_exc:
                logger.error("Failed to store structured audit in MongoDB: %s", db_exc)
                
    except Exception as exc:
        logger.error("Unhandled error in analyze: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/analysis-jobs", response_model=AnalysisJobAccepted, status_code=202, dependencies=[Depends(_require_api_key)])
async def submit_analysis_job(data: URLRequest):
    normalized_url = normalize_url(data.url)

    if not is_valid_url(normalized_url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    return await create_analysis_job(normalized_url)


@router.get("/analysis-jobs/{job_id}", response_model=AnalysisJobStatus, dependencies=[Depends(_require_api_key)])
async def read_analysis_job(job_id: str):
    job = await get_analysis_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    return job


@router.post("/analyze-url/stream", dependencies=[Depends(_require_api_key)])
async def analyze_stream(data: URLRequest):
    normalized_url = normalize_url(data.url)

    if not is_valid_url(normalized_url):
        raise HTTPException(status_code=400, detail="Invalid URL.")

    # StreamingResponse: exceptions inside the generator are caught by
    # analysis_stream.py and emitted as {"type":"error"} NDJSON events,
    # so they never escape to uvicorn as bare text errors.
    return StreamingResponse(
        stream_analysis(normalized_url),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/download-report/{task_id}", dependencies=[Depends(_require_api_key)])
def download_report(task_id: str = Depends(_validate_task_id)):
    """
    Serve the generated SEO report.
    task_id MUST be a valid UUID — any other value returns 400.
    This prevents path traversal attacks via crafted task IDs.
    """
    reports_dir = REPORTS_DIR.resolve()
    pdf_path = (reports_dir / f"{task_id}.pdf").resolve()
    html_path = (reports_dir / f"{task_id}.html").resolve()

    # Double-check resolved path is still inside the reports directory
    if pdf_path.parent != reports_dir or html_path.parent != reports_dir:
        raise HTTPException(status_code=400, detail="Invalid report ID.")

    if pdf_path.exists() and pdf_path.stat().st_size > 0:
        return FileResponse(str(pdf_path), media_type="application/pdf", filename="seo_report.pdf")

    if html_path.exists() and html_path.stat().st_size > 0:
        return FileResponse(str(html_path), media_type="text/html", filename="seo_report.html")

    raise HTTPException(status_code=404, detail="Report not found.")
@router.get("/projects", dependencies=[Depends(_require_api_key)])
async def list_projects():
    return await get_all_projects()


@router.get("/projects/{project_id}", dependencies=[Depends(_require_api_key)])
async def get_project(project_id: str):
    result = await get_project_audit(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    return result
