from __future__ import annotations

import asyncio
import json

from app.core.errors import ServiceError
from app.core.logger import logger
from app.core.openai_client import get_openai_client


def _generate_fix_sync(issue: str) -> dict:
    client = get_openai_client()
    if client is None:
        raise ServiceError(
            "AI fix generation is unavailable because OPENAI_API_KEY is not configured.",
            status_code=503,
        )

    prompt = f"""
    You are an expert SEO web developer diagnosing explicit DOM node hierarchies.
    Provide a robust technical code fix for the following diagnostic issue: "{issue}".

    Explicit Instructions:
    1. Provide a realistic standard HTML snippet demonstrating how this issue currently manifests ("current_code").
    2. Provide the optimized structural HTML replacement directly fixing the core heuristics ("fixed_code"). Keep the string beautifully indented and production-ready.
    3. Offer a very brief textual rationale detailing why this fix is relevant to engine spiders ("explanation").

    Return STRICT VALID JSON matching exactly this object mapping:
    {{
      "issue": "{issue}",
      "current_code": "<html string>",
      "fixed_code": "<html string>",
      "explanation": "text string"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an automated code fixing engine resolving exact string "
                        "modifications strictly wrapped inside standardized JSON output types."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.choices[0].message.content.strip())
    except Exception as exc:
        logger.exception("Failed to generate an AI fix for issue: %s", issue)
        raise ServiceError(
            "The AI fix service failed to produce a usable response.",
            status_code=502,
        ) from exc

    for key in ["issue", "current_code", "fixed_code", "explanation"]:
        if key not in parsed or not isinstance(parsed[key], str):
            raise ServiceError(
                "The AI fix service returned an invalid response payload.",
                status_code=502,
            )

    return parsed


async def generate_fix(issue: str) -> dict:
    return await asyncio.to_thread(_generate_fix_sync, issue)
