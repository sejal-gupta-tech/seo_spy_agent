import time
import httpx

from app.core.config import HTTP_TIMEOUT_SECONDS
from app.core.logger import logger


async def get_page_speed(url: str) -> dict:
    """
    Measures real HTTP response time (Time To First Byte) and actual HTML size.
    Scores are based on TTFB thresholds aligned with 2026 Core Web Vitals guidance.

    Note: For SPAs (React/Next.js/Vue), this measures the SSR shell delivery time,
    not full Time To Interactive. A PageSpeed Insights integration is needed for full LCP/FID/CLS.
    """
    start_time = time.perf_counter()
    score = 0
    response_time = 0.0
    page_size_kb = 0.0
    status = "Failed"
    content_type = ""

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(HTTP_TIMEOUT_SECONDS, connect=min(4.0, HTTP_TIMEOUT_SECONDS))
        ) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                },
                follow_redirects=True,
            )
            response.raise_for_status()

            response_time = round(time.perf_counter() - start_time, 3)
            # Use actual content length (decompressed bytes after reading)
            page_size_kb = round(len(response.content) / 1024, 2)
            content_type = response.headers.get("content-type", "").split(";")[0].strip()

            # Score based on TTFB thresholds (2026 Core Web Vitals guidance)
            # Good: < 0.8s, Needs improvement: 0.8–1.8s, Poor: > 1.8s
            if response_time < 0.5:
                score = 98
            elif response_time < 0.8:
                score = 90
            elif response_time < 1.2:
                score = 75
            elif response_time < 1.8:
                score = 60
            elif response_time < 3.0:
                score = 35
            else:
                score = 15

            # Penalize large uncompressed page size (indicates missing compression/optimization)
            if page_size_kb > 500:
                score -= 10
            elif page_size_kb > 200:
                score -= 5

            score = max(0, min(100, score))

            if score >= 90:
                status = "Fast"
            elif score >= 60:
                status = "Needs Improvement"
            elif score >= 35:
                status = "Slow"
            else:
                status = "Critical"

    except httpx.TimeoutException:
        score = 0
        status = "Timeout"
        response_time = round(time.perf_counter() - start_time, 3)
    except Exception:
        logger.exception("Page speed probe failed for %s", url)
        score = 0
        status = "Failed"

    return {
        "score": score,
        "response_time": response_time,
        "page_size_kb": page_size_kb,
        "content_type": content_type,
        "status": status,
        "note": (
            "TTFB-based measurement. For full Core Web Vitals (LCP, FID, CLS), "
            "integrate Google PageSpeed Insights API."
        ),
    }
