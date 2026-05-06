from __future__ import annotations

import asyncio
import contextlib
import json
import time
from typing import Any

from app.core.logger import logger
from app.services.scraper import analyze_url
from app.services.db_service import save_audit_report


def _serialize_event(event: dict[str, Any]) -> bytes:
    return (json.dumps(event, ensure_ascii=True) + "\n").encode("utf-8")


async def stream_analysis(url: str, business_type: str = "General"):
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
    started_at = time.perf_counter()

    async def push(event: dict[str, Any]) -> None:
        enriched_event = dict(event)
        enriched_event.setdefault("type", "log")
        enriched_event["elapsed_seconds"] = round(
            time.perf_counter() - started_at,
            2,
        )
        await queue.put(enriched_event)

    async def runner() -> None:
        try:
            result = await analyze_url(url, progress_callback=push)
            if "error" not in result:
                # PERSIST TO DATABASE: This ensures the project shows up in "All Projects"
                try:
                    await save_audit_report(url, business_type, result)
                    logger.info(f"Streamed analysis for {url} saved to database.")
                except Exception as db_exc:
                    logger.error(f"Failed to save streamed audit for {url}: {db_exc}")

                await push({"type": "result", "payload": result})
        except Exception:
            logger.exception("Streaming analysis failed for %s", url)
            await push({"type": "error", "detail": "Internal server error while streaming analysis."})
        finally:
            await queue.put({"type": "stream_end"})

    task = asyncio.create_task(runner())

    try:
        while True:
            event = await queue.get()
            if event.get("type") == "stream_end":
                break
            yield _serialize_event(event)
    finally:
        if not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
