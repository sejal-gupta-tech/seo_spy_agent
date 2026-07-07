import asyncio
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import uuid4

from app.core.logger import logger
from app.services.db_service import get_project_audit
from app.services.report_generator import render_report_html, generate_pdf_report

_export_jobs: dict[str, dict[str, Any]] = {}
_export_tasks: dict[str, asyncio.Task[None]] = {}
_export_lock = RLock()

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

async def _run_export_job(job_id: str, project_id: str) -> None:
    with _export_lock:
        job = _export_jobs[job_id]
        job["status"] = "processing"
        job["started_at"] = _utcnow_iso()

    try:
        logger.info(f"Starting performance PDF export for project: {project_id}")
        
        # 1. Fetch project data
        project_data = await get_project_audit(project_id)
        if not project_data:
            raise ValueError("Project data not found")
            
        with _export_lock:
            _export_jobs[job_id]["progress"] = 25
            
        # 2. Extract performance data from crawled pages
        crawl_overview = project_data.get("crawl_overview", {})
        sampled_pages = crawl_overview.get("sampled_pages", [])
        
        if not sampled_pages:
            raise ValueError("No crawled pages found in the project")
            
        with _export_lock:
            _export_jobs[job_id]["progress"] = 50
            _export_jobs[job_id]["total_pages"] = len(sampled_pages)

        # 3. Calculate summary metrics (handling missing values cleanly)
        processed_pages = 0
        perf_pages_count = 0
        mob_score_total = 0
        desk_score_total = 0
        
        for p in sampled_pages:
            perf = p.get("performance", {})
            m_score = perf.get("mobile", {}).get("score")
            d_score = perf.get("desktop", {}).get("score")
            if m_score is not None or d_score is not None:
                perf_pages_count += 1
            if m_score is not None:
                mob_score_total += m_score
            if d_score is not None:
                desk_score_total += d_score
            processed_pages += 1
            
        mob_avg = int(mob_score_total / perf_pages_count) if perf_pages_count > 0 else 0
        desk_avg = int(desk_score_total / perf_pages_count) if perf_pages_count > 0 else 0
            
        summary_metrics = {
            "total_crawled": len(sampled_pages),
            "total_with_performance": perf_pages_count,
            "mobile_avg": mob_avg,
            "desktop_avg": desk_avg,
            "missing_data": len(sampled_pages) - perf_pages_count,
        }
            
        with _export_lock:
            _export_jobs[job_id]["processed_pages"] = processed_pages
            _export_jobs[job_id]["progress"] = 75
            
        # 4. Generate HTML using the new performance template
        template_data = {
            "domain": project_data.get("url", ""),
            "generated_date": datetime.now().strftime("%Y-%m-%d"),
            "summary": summary_metrics,
            "pages": sampled_pages
        }
        
        html_content = render_report_html(template_data, "performance_report.html")
        
        # 5. Generate PDF
        task_id_for_pdf = generate_pdf_report(html_content)
        
        # We will reuse the actual task_id generated inside `generate_pdf_report`.
        # However, it saves it as {task_id_for_pdf}.pdf.
        # We need the user to be able to download it, so we store this task_id.
        
        with _export_lock:
            job = _export_jobs[job_id]
            job["finished_at"] = _utcnow_iso()
            job["status"] = "completed"
            job["progress"] = 100
            job["download_ready"] = True
            job["pdf_task_id"] = task_id_for_pdf

        logger.info(f"Performance PDF export completed successfully. PDF ID: {task_id_for_pdf}")
        
    except Exception as e:
        logger.exception("Performance PDF export %s failed for project %s", job_id, project_id)
        with _export_lock:
            job = _export_jobs[job_id]
            job["status"] = "failed"
            job["error"] = str(e)
            job["finished_at"] = _utcnow_iso()
    finally:
        _export_tasks.pop(job_id, None)

async def create_performance_export_job(project_id: str) -> dict[str, Any]:
    job_id = str(uuid4())
    job_record = {
        "job_id": job_id,
        "project_id": project_id,
        "status": "queued",
        "progress": 0,
        "total_pages": 0,
        "processed_pages": 0,
        "download_ready": False,
        "pdf_task_id": None,
        "created_at": _utcnow_iso(),
        "started_at": None,
        "finished_at": None,
        "error": None,
    }

    with _export_lock:
        _export_jobs[job_id] = job_record

    _export_tasks[job_id] = asyncio.create_task(_run_export_job(job_id, project_id))

    return {
        "job_id": job_id,
        "status": "queued"
    }

async def get_export_job(job_id: str) -> dict[str, Any] | None:
    with _export_lock:
        job = _export_jobs.get(job_id)
        if job is None:
            return None
        return dict(job)
