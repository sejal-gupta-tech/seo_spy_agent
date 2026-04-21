import asyncio
from app.services.scraper import analyze_url

async def test_run():
    print("Testing crawler + PDF fallback pipeline...")
    raw_response = await analyze_url("https://books.toscrape.com/")
    print(f"Report URL output: {raw_response.get('report_url')}")

if __name__ == "__main__":
    asyncio.run(test_run())
