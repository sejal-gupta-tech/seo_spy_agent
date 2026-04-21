import asyncio
import traceback
from app.services.scraper import analyze_url

async def debug_run():
    print("Running analyze_url...")
    try:
        raw_response = await analyze_url("https://books.toscrape.com/")
        print("Crawler finished! Attempting schema validation...")
        from app.models.schema import FinalResponse
        FinalResponse(**raw_response)
        print("Validated successfully!")
    except Exception as e:
        print("EXCEPTION CAUGHT:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_run())
