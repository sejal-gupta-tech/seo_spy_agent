from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from openai import OpenAI

from app.core.logger import logger

load_dotenv()


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY is not configured. AI features will run in degraded mode.")
        return None

    try:
        return OpenAI(api_key=api_key)
    except Exception:
        logger.exception("Failed to initialize OpenAI client.")
        return None
