"""
test_routes.py — Integration tests for the FastAPI route layer.

Tests cover:
  - GET  /docs                         — API docs are reachable
  - POST /analyze-url                  — URL validation, error handling, response shape
  - POST /analyze-url/stream           — streaming endpoint reachability and NDJSON format
  - POST /generate-fix                 — fix generation endpoint
  - GET  /download-report/{task_id}    — path traversal protection, 404 handling

All expensive service calls (crawl, audit, AI) are mocked so tests run instantly.
"""

import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# A minimal but schema-valid FinalResponse payload for mocking analyze_url()
# ---------------------------------------------------------------------------
MOCK_FINAL_RESPONSE = {
    "url": "https://example.com",
    "favicon_status": "Missing",
    "robots_status": "Found (Valid)",
    "sitemap_status": "Found (Valid)",
    "overall_seo_health": "72%",
    "domain_authority": 45,
    "broken_internal_link_ratio": "0%",
    "sampled_pages": [],
    "findings": [],
    "metric_summary": [],
    "category_scores": {
        "metadata": "70%",
        "content_depth": "65%",
        "indexation_governance": "80%",
        "serp_enhancements": "50%",
    },
    "crawl_overview": {
        "analyzed_pages": 5,
        "discovered_internal_pages": 10,
        "sample_coverage_ratio": "50%",
        "crawl_depth": 2,
        "favicon_status": "Missing",
        "broken_internal_link_ratio": "0%",
    },
    "executive_summary": "Example site shows moderate SEO maturity.",
    "management_summary": {
        "board_verdict": "Moderate SEO maturity.",
        "strongest_asset": "Internal linking is solid.",
        "biggest_risk": "Meta descriptions missing on 40% of pages.",
        "growth_opportunity": "Expand content around primary service keywords.",
        "confidence_note": "Medium confidence.",
    },
    "recommended_roadmap": [],
    "market_opportunities": [],
    "keyword_overlap_score": "60%",
    "content_gap_ratio": "40%",
    "content_strategy": {"blog_suggestions": [], "guest_post_titles": []},
    "keyword_analysis": {"primary_keyword": "seo", "keywords": []},
    "page_speed": {"score": 80, "response_time": 0.9, "page_size_kb": 120, "status": "Fast"},
    "link_analysis": {"internal_link_score": 85, "issues": [], "recommendations": []},
    "ai_insights": {"insights": []},
    "report_url": "/download-report/00000000-0000-0000-0000-000000000001",
    "data_limitations": [],
}


# ===========================================================================
# Smoke tests — basic reachability
# ===========================================================================

class TestApiDocs:
    def test_openapi_json_returns_200(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_docs_page_returns_200(self):
        response = client.get("/docs")
        assert response.status_code == 200


# ===========================================================================
# POST /analyze-url — URL validation
# ===========================================================================

class TestAnalyzeUrlValidation:
    def test_rejects_empty_url(self):
        response = client.post("/analyze-url", json={"url": ""})
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_rejects_non_url_string(self):
        response = client.post("/analyze-url", json={"url": "not-a-url"})
        assert response.status_code == 400

    def test_rejects_ftp_url(self):
        response = client.post("/analyze-url", json={"url": "ftp://example.com"})
        assert response.status_code == 400

    def test_rejects_missing_url_field(self):
        response = client.post("/analyze-url", json={})
        assert response.status_code == 422  # Pydantic validation error

    def test_accepts_https_url(self):
        with patch("app.api.routes.analyze_url", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = MOCK_FINAL_RESPONSE
            response = client.post("/analyze-url", json={"url": "https://example.com"})
        assert response.status_code == 200

    def test_accepts_url_without_scheme(self):
        """normalize_url() should add https:// automatically."""
        with patch("app.api.routes.analyze_url", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = MOCK_FINAL_RESPONSE
            response = client.post("/analyze-url", json={"url": "example.com"})
        assert response.status_code == 200

    def test_returns_json_content_type(self):
        with patch("app.api.routes.analyze_url", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = MOCK_FINAL_RESPONSE
            response = client.post("/analyze-url", json={"url": "https://example.com"})
        assert "application/json" in response.headers["content-type"]


# ===========================================================================
# POST /analyze-url — response shape
# ===========================================================================

class TestAnalyzeUrlResponseShape:
    @pytest.fixture(autouse=True)
    def mock_analyze(self):
        with patch("app.api.routes.analyze_url", new_callable=AsyncMock) as m:
            m.return_value = MOCK_FINAL_RESPONSE
            yield m

    def test_response_contains_overall_seo_health(self):
        response = client.post("/analyze-url", json={"url": "https://example.com"})
        data = response.json()
        assert "overall_seo_health" in data

    def test_response_contains_crawl_overview(self):
        response = client.post("/analyze-url", json={"url": "https://example.com"})
        data = response.json()
        assert "crawl_overview" in data

    def test_response_contains_findings(self):
        response = client.post("/analyze-url", json={"url": "https://example.com"})
        data = response.json()
        assert "findings" in data
        assert isinstance(data["findings"], list)

    def test_response_contains_management_summary(self):
        response = client.post("/analyze-url", json={"url": "https://example.com"})
        data = response.json()
        assert "management_summary" in data
        mgmt = data["management_summary"]
        assert "board_verdict" in mgmt

    def test_service_error_returns_500(self):
        with patch("app.api.routes.analyze_url", new_callable=AsyncMock) as mock_err:
            mock_err.side_effect = RuntimeError("database exploded")
            response = client.post("/analyze-url", json={"url": "https://example.com"})
        assert response.status_code == 500
        assert "application/json" in response.headers["content-type"]

    def test_service_error_message_not_bare_text(self):
        """BUG FIX: errors must be JSON, not bare uvicorn text/plain."""
        with patch("app.api.routes.analyze_url", new_callable=AsyncMock) as mock_err:
            mock_err.side_effect = Exception("some internal crash")
            response = client.post("/analyze-url", json={"url": "https://example.com"})
        assert response.status_code == 500
        # Must be parseable as JSON
        data = response.json()
        assert "detail" in data


# ===========================================================================
# POST /analyze-url/stream
# ===========================================================================

class TestAnalyzeUrlStream:
    def test_valid_url_returns_200(self):
        async def mock_stream(url):
            yield b'{"type": "run_started", "url": "https://example.com"}\n'
            yield b'{"type": "stream_end"}\n'

        with patch("app.api.routes.stream_analysis", return_value=mock_stream("https://example.com")):
            response = client.post(
                "/analyze-url/stream",
                json={"url": "https://example.com"},
            )
        assert response.status_code == 200

    def test_rejects_invalid_url(self):
        response = client.post("/analyze-url/stream", json={"url": "not-a-url"})
        assert response.status_code == 400

    def test_content_type_is_ndjson(self):
        async def mock_stream(url):
            yield b'{"type": "run_started"}\n'

        with patch("app.api.routes.stream_analysis", return_value=mock_stream("x")):
            response = client.post(
                "/analyze-url/stream",
                json={"url": "https://example.com"},
            )
        assert "ndjson" in response.headers.get("content-type", "").lower()

    def test_stream_lines_are_valid_json(self):
        events = [
            b'{"type": "run_started", "url": "https://example.com"}\n',
            b'{"type": "stage", "stage": "crawl", "status": "active"}\n',
            b'{"type": "result", "payload": {}}\n',
        ]

        async def mock_stream(url):
            for event in events:
                yield event

        with patch("app.api.routes.stream_analysis", return_value=mock_stream("x")):
            response = client.post(
                "/analyze-url/stream",
                json={"url": "https://example.com"},
            )

        for line in response.content.splitlines():
            if line.strip():
                parsed = json.loads(line)
                assert "type" in parsed


# ===========================================================================
# POST /generate-fix
# ===========================================================================

class TestGenerateFix:
    def test_valid_issue_returns_fix(self):
        with patch("app.api.routes.generate_fix", new_callable=AsyncMock) as mock_fix:
            mock_fix.return_value = {
                "issue": "Missing meta description",
                "fix": '<meta name="description" content="Your page description here.">',
                "explanation": "Add a 140-160 char meta description.",
            }
            response = client.post("/generate-fix", json={"issue": "Missing meta description"})
        assert response.status_code == 200

    def test_rejects_missing_issue_field(self):
        response = client.post("/generate-fix", json={})
        assert response.status_code == 422

    def test_service_error_returns_500(self):
        with patch("app.api.routes.generate_fix", new_callable=AsyncMock) as mock_fix:
            mock_fix.side_effect = Exception("OpenAI timeout")
            response = client.post("/generate-fix", json={"issue": "Missing title"})
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


# ===========================================================================
# GET /download-report/{task_id}
# ===========================================================================

class TestDownloadReport:
    def test_rejects_path_traversal(self):
        """BUG FIX: ../etc/passwd style IDs must be rejected."""
        response = client.get("/download-report/../../etc/passwd")
        assert response.status_code in {400, 404}

    def test_rejects_non_uuid_id(self):
        response = client.get("/download-report/abc123-not-a-uuid")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_rejects_empty_id(self):
        # Empty path segment → 404 from routing
        response = client.get("/download-report/")
        assert response.status_code in {404, 405}

    def test_valid_uuid_but_no_file_returns_404(self):
        response = client.get("/download-report/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_valid_uuid_with_existing_pdf_returns_200(self, tmp_path):
        task_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        reports_dir = os.path.abspath("reports")
        os.makedirs(reports_dir, exist_ok=True)
        pdf_path = os.path.join(reports_dir, f"{task_id}.pdf")

        try:
            with open(pdf_path, "wb") as f:
                f.write(b"%PDF-1.4 fake pdf content")

            response = client.get(f"/download-report/{task_id}")
            assert response.status_code == 200
            assert "pdf" in response.headers.get("content-type", "").lower()
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

    def test_uuid_with_uppercase_is_accepted(self):
        """UUIDs are case-insensitive — uppercase should also be valid format."""
        response = client.get("/download-report/AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE")
        # Should not be 400 (format valid), but 404 (no file)
        assert response.status_code == 404


# ===========================================================================
# API key authentication (when enabled)
# ===========================================================================

class TestApiKeyAuth:
    def test_no_key_required_when_env_empty(self):
        """When SEO_SPY_API_KEY is not set, all endpoints are open."""
        with patch.dict(os.environ, {"SEO_SPY_API_KEY": ""}):
            # Reimport routes to pick up empty key
            import importlib
            import app.api.routes as routes_module
            importlib.reload(routes_module)
            # Re-create test client with reloaded app
            response = client.post("/analyze-url", json={"url": "not-a-url"})
            # Should get 400 (URL validation) not 403 (auth)
            assert response.status_code == 400

    def test_wrong_key_returns_403_when_key_configured(self):
        """When SEO_SPY_API_KEY is set, wrong key → 403."""
        with patch("app.api.routes._API_KEY_ENV", "secret-key-123"):
            response = client.post(
                "/analyze-url",
                json={"url": "https://example.com"},
                headers={"X-API-Key": "wrong-key"},
            )
        assert response.status_code == 403

    def test_correct_key_passes_auth(self):
        """Correct key + invalid URL → 400, not 403."""
        with patch("app.api.routes._API_KEY_ENV", "secret-key-123"):
            response = client.post(
                "/analyze-url",
                json={"url": "not-a-url"},
                headers={"X-API-Key": "secret-key-123"},
            )
        assert response.status_code == 400  # Auth passed, URL invalid
