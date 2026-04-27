import logging
import os
import traceback

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load .env before anything else so OPENAI_API_KEY and friends are available
# to every module imported below.
load_dotenv()

from app.api.routes import router  # noqa: E402 — must come after load_dotenv()
from app.core.database import db_manager # noqa: E402

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SEO Spy Agent",
    description="AI-powered SEO audit and analysis API.",
    version="1.0.0",
)

@app.on_event("startup")
async def startup():
    await db_manager.connect()

@app.on_event("shutdown")
async def shutdown():
    await db_manager.close()

# ---------------------------------------------------------------------------
# CORS
# Allow the Next.js frontend (and any origins listed in ALLOWED_ORIGINS) to
# reach the API. In production, restrict this to your actual frontend domain.
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handler
# Catches any unhandled exception that escapes a route and returns a
# structured JSON 500 instead of uvicorn's bare "Internal Server Error" text.
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def _global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception on %s %s: %s\n%s",
        request.method,
        request.url.path,
        exc,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected server error occurred: {type(exc).__name__}: {exc}"},
    )


@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "SEO Spy Agent API is running.",
        "documentation": "/docs"
    }


app.include_router(router)
