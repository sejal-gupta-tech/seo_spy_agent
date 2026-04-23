from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import uuid4

from app.core.logger import logger
from app.services.scraper import analyze_url

_RECENT_EVENT_LIMIT = 50
_jobs: dict[str, dict[str, Any]] = {}
_tasks: dict[str, asyncio.Task[None]] = {}
_jobs_lock = RLock()


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialize_job(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": job["job_id"],
        "url": job["url"],
        "status": job["status"],
        "created_at": job["created_at"],
        "started_at": job.get("started_at"),
        "finished_at": job.get("finished_at"),
        "error": job.get("error"),
        "latest_event": job.get("latest_event"),
        "recent_events": list(job.get("recent_events", [])),
        "result": job.get("result"),
    }


async def _append_event(job_id: str, event: dict[str, Any]) -> None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return

        copied_event = dict(event)
        recent_events = job["recent_events"]
        recent_events.append(copied_event)
        if len(recent_events) > _RECENT_EVENT_LIMIT:
            recent_events.popleft()

        job["latest_event"] = copied_event


async def _run_job(job_id: str, url: str) -> None:
    with _jobs_lock:
        job = _jobs[job_id]
        job["status"] = "running"
        job["started_at"] = _utcnow_iso()

    try:
        result = await analyze_url(url, progress_callback=lambda event: _append_event(job_id, event))

        with _jobs_lock:
            job = _jobs[job_id]
            job["finished_at"] = _utcnow_iso()
            if "error" in result:
                job["status"] = "failed"
                job["error"] = result["error"]
            else:
                job["status"] = "completed"
                job["result"] = result
    except Exception:
        logger.exception("Analysis job %s failed for URL %s", job_id, url)
        with _jobs_lock:
            job = _jobs[job_id]
            job["status"] = "failed"
            job["error"] = "Internal server error while running the analysis job."
            job["finished_at"] = _utcnow_iso()
    finally:
        _tasks.pop(job_id, None)


async def create_analysis_job(url: str) -> dict[str, Any]:
    job_id = str(uuid4())
    job_record = {
        "job_id": job_id,
        "url": url,
        "status": "queued",
        "created_at": _utcnow_iso(),
        "started_at": None,
        "finished_at": None,
        "error": None,
        "latest_event": None,
        "recent_events": deque(),
        "result": None,
    }

    with _jobs_lock:
        _jobs[job_id] = job_record

    _tasks[job_id] = asyncio.create_task(_run_job(job_id, url))

    return {
        "job_id": job_id,
        "url": url,
        "status": "queued",
        "created_at": job_record["created_at"],
        "status_url": f"/analysis-jobs/{job_id}",
    }


async def get_analysis_job(job_id: str) -> dict[str, Any] | None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return None
        return _serialize_job(job)
