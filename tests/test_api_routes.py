import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.errors import ServiceError
from app.main import app


def _build_final_response(url: str = "https://example.com/") -> dict:
    page_summary = {
        "url": url,
        "page_type": "Homepage",
        "title": "Example Title",
        "word_count": 420,
        "seo_health": "92%",
        "key_issue": "Missing FAQ schema",
        "canonical_url": url,
        "has_canonical": True,
        "page_authority": 24,
        "dofollow_links": 5,
        "nofollow_links": 0,
        "url_structure": {
            "is_seo_friendly": True,
            "issues": [],
            "recommendations": [],
            "score": 95,
        },
    }
    metric_summary = [
        {
            "metric": "Title Coverage",
            "current_value": "100%",
            "benchmark": "90%+",
            "status": "Passed",
        }
    ]
    findings = [
        {
            "category": "Metadata",
            "metric": "Meta Description Coverage",
            "current_value": "80%",
            "benchmark": "85%+",
            "status": "Warning",
            "business_impact": "Some pages may underperform in SERPs.",
            "recommendation": "Add missing meta descriptions.",
            "priority": "High",
            "evidence": [],
        }
    ]
    management_summary = {
        "board_verdict": "Healthy technical foundation with execution gaps.",
        "strongest_asset": "Title coverage is consistent.",
        "biggest_risk": "Schema coverage is incomplete.",
        "growth_opportunity": "Expand structured content around commercial terms.",
        "confidence_note": "Medium confidence based on sampled crawl data.",
    }
    content_strategy = {
        "blog_suggestions": [
            {
                "title": "How to Audit SEO Faster",
                "target_audience": "Marketing leads",
                "search_intent": "informational",
                "outline": ["Introduction", "Framework", "Execution"],
            }
        ],
        "guest_post_titles": ["How AI changes technical SEO audits"],
    }
    keyword_analysis = {
        "primary_keywords": ["seo audit"],
        "long_tail_keywords": ["ai seo audit tool"],
        "keyword_intent": {
            "informational": ["seo audit"],
            "transactional": ["ai seo audit tool"],
            "navigational": [],
        },
    }
    page_speed = {
        "score": 91,
        "response_time": 0.64,
        "page_size_kb": 148.2,
        "status": "Fast",
    }
    link_analysis = {
        "internal": {
            "internal_link_score": 88,
            "issues": [],
            "recommendations": ["Add contextual links to pricing pages."],
        },
        "external": {
            "total_external_links": 2,
            "domains": ["example.org"],
        },
        "backlinks": {
            "backlink_strength": "Medium",
            "estimated_backlinks": 12,
            "referring_domains": 5,
        },
    }
    ai_insights = {
        "insights": [
            {
                "issue": "Schema coverage",
                "impact": "High",
                "priority": "High",
                "explanation": "Missing schema reduces eligibility for rich results.",
                "recommendation": "Add structured data to key landing pages.",
            }
        ]
    }
    market_opportunities = [
        {
            "keyword": "technical seo audit",
            "market_opportunity_score": 8,
            "relevance_to_business": "Aligned to the site's service offering.",
            "supporting_gap_ratio": "40%",
            "business_impact": "Can grow qualified demand.",
            "recommendation": "Create a dedicated commercial landing page.",
            "priority": "High",
        }
    ]
    roadmap = [
        {
            "timeline": "0-30 days",
            "priority": "High",
            "objective": "Close metadata and schema gaps.",
            "actions": ["Ship meta descriptions", "Add schema to service pages"],
            "expected_outcome": "Improved index quality and richer SERP coverage.",
        }
    ]
    data_limitations = [
        {
            "data_source": "Analytics",
            "current_status": "Not connected",
            "why_it_matters": "Conversion impact cannot be quantified.",
            "next_step": "Connect analytics and search console data.",
        }
    ]

    return {
        "executive_summary": "The site has a solid technical base with a few high-impact gaps.",
        "management_summary": management_summary,
        "crawl_overview": {
            "analyzed_pages": 1,
            "discovered_internal_pages": 1,
            "sample_coverage_ratio": "100%",
            "crawl_depth": 1,
            "robots_txt_status": "Found (200)",
            "sitemap_status": "Found (Valid)",
            "favicon_status": "Found (HTML meta tag)",
            "domain_authority": 32,
            "broken_internal_link_ratio": "0%",
            "sampled_pages": [page_summary],
        },
        "technical_audit": {
            "benchmark_reference_year": 2026,
            "overall_seo_health": "92%",
            "metric_summary": metric_summary,
            "findings": findings,
        },
        "competitive_intelligence": {
            "keyword_overlap_score": "60%",
            "content_gap_ratio": "40%",
            "competitor_sample_size": 2,
            "market_opportunities": market_opportunities,
        },
        "data_limitations": data_limitations,
        "recommended_roadmap": roadmap,
        "detailed_appendix": {
            "primary_page_url": url,
            "primary_page_audit": {
                "benchmark_reference_year": 2026,
                "overall_seo_health": "92%",
                "metric_summary": metric_summary,
                "findings": findings,
            },
            "page_summaries": [page_summary],
            "evidence_notes": ["Single-page synthetic test payload."],
        },
        "pdf_template_data": {
            "report_title": "Management SEO Audit Report",
            "prepared_for": "Management Board",
            "website": url,
            "generated_on": "2026-04-23",
            "executive_summary": "The site has a solid technical base with a few high-impact gaps.",
            "board_verdict": management_summary["board_verdict"],
            "management_summary": management_summary,
            "hero_metrics": [{"label": "SEO Health", "value": "92%"}],
            "crawl_overview": [{"label": "Pages Sampled", "value": "1"}],
            "priority_actions": [
                {
                    "priority": "High",
                    "headline": "Fix schema coverage",
                    "action": "Add structured data to core landing pages.",
                    "business_impact": "Improves rich result eligibility.",
                }
            ],
            "market_opportunities": market_opportunities,
            "technical_findings": findings,
            "metric_summary": metric_summary,
            "recommended_roadmap": roadmap,
            "content_strategy": content_strategy,
            "keyword_analysis": keyword_analysis,
            "page_speed": page_speed,
            "link_analysis": link_analysis,
            "ai_insights": ai_insights["insights"],
            "sampled_pages": [page_summary],
            "competitor_sample_size": 2,
            "keyword_overlap_score": "60%",
            "content_gap_ratio": "40%",
            "data_limitations": data_limitations,
            "company_name": "Example Inc",
            "business_summary": "Synthetic test business summary.",
        },
        "content_strategy": content_strategy,
        "page_speed": page_speed,
        "keyword_analysis": keyword_analysis,
        "link_analysis": link_analysis,
        "ai_insights": ai_insights,
        "report_url": "/download-report/test-report",
    }


class ApiRoutesTestCase(unittest.TestCase):
    def test_generate_fix_returns_503_on_service_failure(self):
        async def fake_generate_fix(_issue: str):
            raise ServiceError("AI fix generation is unavailable.", status_code=503)

        with patch("app.api.routes.generate_fix", new=fake_generate_fix):
            with TestClient(app) as client:
                response = client.post("/generate-fix", json={"issue": "Missing meta description"})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "AI fix generation is unavailable."})

    def test_download_report_missing_returns_404(self):
        with TestClient(app) as client:
            response = client.get("/download-report/not-found")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Report not found"})

    def test_download_report_returns_html_fallback(self):
        with TemporaryDirectory() as tmp_dir:
            report_dir = Path(tmp_dir)
            (report_dir / "sample.html").write_text("<html><body>fallback</body></html>", encoding="utf-8")

            with patch("app.api.routes.REPORTS_DIR", report_dir):
                with TestClient(app) as client:
                    response = client.get("/download-report/sample")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["content-type"].startswith("text/html"))
        self.assertIn("fallback", response.text)

    def test_submit_analysis_job_and_poll_result(self):
        async def fake_analyze_url(url: str, progress_callback=None):
            if progress_callback is not None:
                await progress_callback(
                    {
                        "type": "stage",
                        "stage": "crawl",
                        "status": "active",
                        "label": "Mapping crawl frontier",
                        "detail": "Collecting HTML pages.",
                    }
                )
            return _build_final_response(url)

        with patch("app.services.analysis_jobs.analyze_url", new=fake_analyze_url):
            with TestClient(app) as client:
                submit_response = client.post("/analysis-jobs", json={"url": "example.com"})
                self.assertEqual(submit_response.status_code, 202)
                payload = submit_response.json()
                job_id = payload["job_id"]
                self.assertEqual(payload["status_url"], f"/analysis-jobs/{job_id}")

                final_response = None
                for _ in range(30):
                    status_response = client.get(f"/analysis-jobs/{job_id}")
                    self.assertEqual(status_response.status_code, 200)
                    final_response = status_response.json()
                    if final_response["status"] == "completed":
                        break
                    time.sleep(0.01)

        self.assertIsNotNone(final_response)
        self.assertEqual(final_response["status"], "completed")
        self.assertEqual(final_response["result"]["report_url"], "/download-report/test-report")
        self.assertEqual(final_response["latest_event"]["stage"], "crawl")

    def test_analysis_job_missing_returns_404(self):
        with TestClient(app) as client:
            response = client.get("/analysis-jobs/missing-job")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Analysis job not found"})


if __name__ == "__main__":
    unittest.main()
