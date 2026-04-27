"""
Shared pytest fixtures and configuration for the SEO Spy Agent test suite.
Run all tests with:  venv\Scripts\pytest tests/ -v
"""
import os
import pytest

# ---------------------------------------------------------------------------
# Load .env before any app module is imported, just like main.py does.
# ---------------------------------------------------------------------------
from dotenv import load_dotenv
load_dotenv()


# ---------------------------------------------------------------------------
# Shared sample data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_page() -> dict:
    """A realistic parsed page dict that mirrors what _parse_page() returns."""
    return {
        "url": "https://example.com/services/seo-audit",
        "depth": 1,
        "status_code": 200,
        "title": "Professional SEO Audit Services | Example Agency",
        "title_length": 47,
        "description": "Get a comprehensive SEO audit from our expert team. We identify technical issues, content gaps, and growth opportunities for your website.",
        "meta_description_length": 137,
        "canonical_url": "https://example.com/services/seo-audit",
        "has_canonical": True,
        "favicon_url": "https://example.com/favicon.ico",
        "has_favicon": True,
        "has_viewport_meta": True,
        "robots_directives": "",
        "is_indexable": True,
        "headings": {
            "h1": ["Expert SEO Audit Services"],
            "h2": ["What We Audit", "Our Process", "Pricing"],
            "h3": ["Technical SEO", "Content Gaps", "Backlink Profile"],
            "h4": [], "h5": [], "h6": [],
        },
        "h1_count": 1,
        "word_count": 850,
        "total_images": 6,
        "missing_alt_images": [],
        "internal_links_count": 14,
        "external_links_count": 3,
        "internal_links": [
            "https://example.com/",
            "https://example.com/about",
            "https://example.com/contact",
        ],
        "internal_link_anchors": ["Home", "About Us", "Contact"],
        "internal_link_targets": [
            "https://example.com/",
            "https://example.com/about",
            "https://example.com/contact",
        ],
        "external_links": ["https://google.com", "https://moz.com", "https://ahrefs.com"],
        "external_domains": ["google.com", "moz.com", "ahrefs.com"],
        "dofollow_links": 16,
        "nofollow_links": 1,
        "has_open_graph": True,
        "has_twitter_card": False,
        "has_structured_data": True,
        "structured_data_types": ["Service", "Organization"],
        "page_type": "Service",
        "page_authority": 55,
        "url_structure": {
            "url": "https://example.com/services/seo-audit",
            "is_seo_friendly": True,
            "score": 100,
            "issues": [],
            "recommendations": [],
            "depth": 2,
        },
    }


@pytest.fixture
def thin_page(sample_page) -> dict:
    """A page with many SEO deficiencies."""
    p = dict(sample_page)
    p.update({
        "url": "https://example.com/thin",
        "title": "Page",
        "title_length": 4,
        "description": "",
        "meta_description_length": 0,
        "canonical_url": "",
        "has_canonical": False,
        "has_favicon": False,
        "favicon_url": "",
        "has_viewport_meta": False,
        "robots_directives": "noindex",
        "is_indexable": False,
        "headings": {"h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []},
        "h1_count": 0,
        "word_count": 45,
        "total_images": 4,
        "missing_alt_images": ["img1.jpg", "img2.jpg", "img3.jpg"],
        "internal_links_count": 1,
        "external_links_count": 0,
        "has_open_graph": False,
        "has_twitter_card": False,
        "has_structured_data": False,
        "structured_data_types": [],
        "page_type": "Other",
    })
    return p


@pytest.fixture
def sample_crawl_data(sample_page, thin_page) -> dict:
    """Minimal crawl_data dict that mirrors what crawl_site() returns."""
    return {
        "base_url": "https://example.com",
        "domain": "example.com",
        "pages": [sample_page, thin_page],
        "primary_page": sample_page,
        "analyzed_pages": 2,
        "discovered_internal_pages": 10,
        "sample_coverage_ratio": 20.0,
        "crawl_depth": 2,
        "robots": {
            "url": "https://example.com/robots.txt",
            "status_code": 200,
            "exists": True,
            "status_string": "Found (Valid)",
            "body": "User-agent: *\nDisallow: /admin\nSitemap: https://example.com/sitemap.xml",
        },
        "sitemap": {
            "url": "https://example.com/sitemap.xml",
            "status_code": 200,
            "exists": True,
            "status_string": "Found (Valid)",
            "body": "<urlset><url><loc>https://example.com/</loc></url></urlset>",
        },
        "favicon": {
            "url": "https://example.com/favicon.ico",
            "status_code": 200,
            "exists": True,
            "content_type": "image/x-icon",
            "status_string": "Found (200 · image/x-icon)",
        },
        "declared_sitemaps": ["https://example.com/sitemap.xml"],
        "broken_link_summary": {
            "checked_count": 5,
            "broken_count": 0,
            "broken_ratio": 0.0,
            "broken_links": [],
        },
    }
