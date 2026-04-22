from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Any

ProgressEvent = dict[str, Any]
ProgressCallback = Callable[[ProgressEvent], Awaitable[None] | None]


async def emit_progress(
    callback: ProgressCallback | None,
    event: ProgressEvent,
) -> None:
    if callback is None:
        return

    maybe_awaitable = callback(event)
    if inspect.isawaitable(maybe_awaitable):
        await maybe_awaitable
