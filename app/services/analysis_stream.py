from __future__ import annotations

import asyncio
import contextlib
import json
import time
from typing import Any

from app.services.scraper import analyze_url


def _serialize_event(event: dict[str, Any]) -> bytes:
    return (json.dumps(event, ensure_ascii=True) + "\n").encode("utf-8")


async def stream_analysis(url: str):
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
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
            if "error" in result:
                await push({"type": "error", "detail": result["error"]})
            else:
                await push({"type": "result", "payload": result})
        except Exception as exc:
            await push({"type": "error", "detail": str(exc)})
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
