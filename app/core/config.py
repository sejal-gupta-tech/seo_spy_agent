import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = PROJECT_ROOT / "app" / "templates"

# On Vercel, the filesystem is read-only except for /tmp
if os.getenv("VERCEL") == "1":
    REPORTS_DIR = Path("/tmp/reports")
else:
    REPORTS_DIR = PROJECT_ROOT / "reports"


def _read_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError:
        return default


def _read_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return float(raw_value)
    except ValueError:
        return default


# ---------------------------------------------------------------------------
# Security / CORS
# These are read directly in main.py and routes.py from os.getenv, but
# defining them here gives a single source of truth for documentation.
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]
API_KEY: str = os.getenv("SEO_SPY_API_KEY", "").strip()

# MongoDB settings
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "seo_spy_agent")

SEO_BENCHMARK_YEAR = 2026

DEFAULT_COMPANY_NAME = "This Website"
DEFAULT_REPORT_AUDIENCE = "Management Board"

DEFAULT_SERVICE_PILLARS = [
    "Primary service visibility",
    "Commercial search positioning",
    "Market discovery",
]

DEFAULT_MARKET_FOCUS_KEYWORDS = [
    "primary service",
    "commercial intent",
    "customer demand",
]

# Set SEO_SPY_CRAWL_MAX_PAGES=0 to crawl ALL discovered pages (no limit).
# Default is 500 which is high enough to cover most sites fully.
CRAWL_MAX_PAGES = _read_int("SEO_SPY_CRAWL_MAX_PAGES", 500)
CRAWL_MAX_DEPTH = _read_int("SEO_SPY_CRAWL_MAX_DEPTH", 5)
BROKEN_LINK_CHECK_LIMIT = _read_int("SEO_SPY_BROKEN_LINK_CHECK_LIMIT", 20)
HTTP_TIMEOUT_SECONDS = _read_float("SEO_SPY_HTTP_TIMEOUT_SECONDS", 8.0)
COMPETITOR_FETCH_TIMEOUT_SECONDS = _read_float(
    "SEO_SPY_COMPETITOR_FETCH_TIMEOUT_SECONDS",
    5.0,
)
CRAWL_RETRY_DELAY_SECONDS = _read_float("SEO_SPY_CRAWL_RETRY_DELAY_SECONDS", 0.35)

SEO_BENCHMARKS = {
    "title_length": {
        "min": 50,
        "max": 60,
        "label": "50-60 characters",
    },
    "meta_description_length": {
        "min": 140,
        "max": 160,
        "label": "140-160 characters",
    },
    "h1_count": {
        "target": 1,
        "label": "Exactly 1 H1",
    },
    "viewport_meta": {
        "target": True,
        "label": "Viewport meta present for mobile-first indexing",
    },
    "alt_text_coverage": {
        "target": 100,
        "label": "100% descriptive alt-text coverage",
    },
    "internal_link_density": {
        "min": 65,
        "max": 100,
        "label": "65%+ internal link density",
    },
    "canonical": {
        "target": True,
        "label": "Self-referencing canonical tag present",
    },
}

# New Production-Ready Weights (must sum to 100)
AUDIT_WEIGHTS = {
    "metadata": 20,
    "headings": 20,
    "technical": 20,
    "performance": 15,
    "links": 15,
    "accessibility": 10,
}

SITEWIDE_BENCHMARKS = {
    "title_coverage": {
        "min": 90,
        "label": "90%+ sampled pages with optimized titles",
    },
    "meta_description_coverage": {
        "min": 85,
        "label": "85%+ sampled pages with optimized meta descriptions",
    },
    "h1_compliance": {
        "min": 90,
        "label": "90%+ sampled pages with exactly one H1",
    },
    "canonical_coverage": {
        "min": 95,
        "label": "95%+ sampled pages with canonical tags",
    },
    "indexability_coverage": {
        "min": 90,
        "label": "90%+ sampled pages indexable unless intentionally excluded",
    },
    "structured_data_coverage": {
        "min": 50,
        "label": "50%+ sampled pages with structured data",
    },
    "social_metadata_coverage": {
        "min": 80,
        "label": "80%+ sampled pages with Open Graph or Twitter metadata",
    },
    "substantive_content_coverage": {
        "min": 70,
        "label": "70%+ sampled pages with at least 300 words of substantive copy",
    },
    "alt_text_coverage": {
        "min": 95,
        "label": "95%+ sitewide alt-text coverage across sampled images",
    },
    "broken_internal_link_ratio": {
        "max": 2,
        "label": "0-2% broken internal links across checked samples",
    },
    "unique_title_coverage": {
        "min": 100,
        "label": "100% unique titles across sampled pages",
    },
    "unique_meta_coverage": {
        "min": 100,
        "label": "100% unique meta descriptions across sampled pages",
    },
}

SITEWIDE_AUDIT_WEIGHTS = {
    "metadata": 30,
    "content": 20,
    "indexation": 20,
    "serp": 15,
    "integrity": 15
}

PRIORITY_ORDER = {
    "High": 0,
    "Medium": 1,
    "Low": 2,
}
