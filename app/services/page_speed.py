import time
import httpx

async def get_page_speed(url: str) -> dict:
    """
    Evaluates basic HTTP performance calculating response elasticity and simulated scoring.
    """
    start_time = time.time()
    score = 0
    response_time = 0.0
    page_size_kb = 0.0
    status = "Failed"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
                },
                follow_redirects=True,
            )
            response.raise_for_status()

            end_time = time.time()
            response_time = round(end_time - start_time, 2)
            page_size_kb = round(len(response.content) / 1024, 2)

            if response_time < 1.0:
                score = 95
            elif response_time < 2.0:
                score = 80
            elif response_time < 3.0:
                score = 60
            else:
                score = 30

            if page_size_kb > 1024:
                score -= 15

            score = max(0, min(100, score))

            if score >= 90:
                status = "Fast"
            elif score >= 50:
                status = "Average"
            else:
                status = "Slow"

    except Exception:
        score = 0
        status = "Failed"

    return {
        "score": score,
        "response_time": response_time,
        "page_size_kb": page_size_kb,
        "status": status,
    }
