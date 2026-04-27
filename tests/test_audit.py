"""
test_audit.py — Unit tests for the SEO Spy Agent audit engine.

Tests cover:
  - Per-page audit: audit_seo()
  - Sitewide audit: audit_sitewide()
  - Individual finding builders (title, meta, h1, canonical, images, mobile, links)
  - Score calculation helpers (weighted_score, range_attainment, priority_from_score)
  - Report builder helpers (build_management_summary, build_executive_summary, build_recommended_roadmap)
"""

import pytest
from app.services.audit import audit_seo, audit_sitewide
from app.utils.helpers import (
    clamp,
    format_percentage,
    priority_from_score,
    range_attainment,
    minimum_attainment,
    maximum_attainment,
    status_from_score,
    weighted_score,
)
from app.services.report_builder import (
    build_management_summary,
    build_executive_summary,
    build_recommended_roadmap,
    build_data_limitations,
)


# ===========================================================================
# Helper utilities
# ===========================================================================

class TestClamp:
    def test_value_within_range(self):
        assert clamp(50.0) == 50.0

    def test_value_below_min(self):
        assert clamp(-10.0) == 0.0

    def test_value_above_max(self):
        assert clamp(150.0) == 100.0

    def test_custom_range(self):
        assert clamp(5.0, 10.0, 20.0) == 10.0


class TestFormatPercentage:
    def test_integer_value(self):
        assert format_percentage(75.0) == "75%"

    def test_decimal_value(self):
        assert format_percentage(72.3) == "72.3%"

    def test_clamped_above_100(self):
        assert format_percentage(120.0) == "100%"

    def test_clamped_below_0(self):
        assert format_percentage(-5.0) == "0%"

    def test_zero(self):
        assert format_percentage(0.0) == "0%"

    def test_100(self):
        assert format_percentage(100.0) == "100%"


class TestPriorityFromScore:
    def test_score_below_60_is_high(self):
        assert priority_from_score(59) == "High"

    def test_score_at_60_is_medium(self):
        assert priority_from_score(60) == "Medium"

    def test_score_at_90_is_low(self):
        assert priority_from_score(90) == "Low"

    def test_score_above_90_is_low(self):
        assert priority_from_score(95) == "Low"

    def test_hard_fail_always_high(self):
        assert priority_from_score(95, hard_fail=True) == "High"


class TestStatusFromScore:
    def test_90_plus_is_at_benchmark(self):
        assert status_from_score(90) == "At Benchmark"

    def test_70_89_is_below_benchmark(self):
        assert status_from_score(75) == "Below Benchmark"

    def test_below_70_is_critical_gap(self):
        assert status_from_score(50) == "Critical Gap"


class TestRangeAttainment:
    def test_within_range_is_100(self):
        assert range_attainment(55, 50, 60) == 100.0

    def test_zero_is_zero(self):
        assert range_attainment(0, 50, 60) == 0.0

    def test_below_min_is_partial(self):
        result = range_attainment(25, 50, 60)
        assert 0 < result < 100

    def test_above_max_is_partial(self):
        result = range_attainment(100, 50, 60)
        assert 0 < result < 100


class TestWeightedScore:
    def test_equal_weights(self):
        scores = {"a": 80.0, "b": 60.0}
        weights = {"a": 1, "b": 1}
        result = weighted_score(scores, weights)
        assert result == 70.0

    def test_higher_weight_dominates(self):
        scores = {"a": 100.0, "b": 0.0}
        weights = {"a": 9, "b": 1}
        result = weighted_score(scores, weights)
        assert result == 90.0

    def test_empty_weights_returns_zero(self):
        assert weighted_score({}, {}) == 0.0

    def test_missing_score_key_treated_as_zero(self):
        result = weighted_score({"a": 80.0}, {"a": 1, "b": 1})
        assert result == 40.0


# ===========================================================================
# audit_seo (per-page audit)
# ===========================================================================

class TestAuditSeo:
    def test_good_page_scores_above_70(self, sample_page):
        result = audit_seo(sample_page)
        assert result["overall_score"] >= 70

    def test_thin_page_scores_below_60(self, thin_page):
        result = audit_seo(thin_page)
        assert result["overall_score"] < 60

    def test_result_has_required_keys(self, sample_page):
        result = audit_seo(sample_page)
        for key in ["overall_score", "overall_seo_health", "findings",
                    "metric_summary", "category_scores"]:
            assert key in result, f"Missing key: {key}"

    def test_overall_seo_health_is_percentage_string(self, sample_page):
        result = audit_seo(sample_page)
        assert result["overall_seo_health"].endswith("%")

    def test_findings_sorted_high_first(self, thin_page):
        result = audit_seo(thin_page)
        priorities = [f["priority"] for f in result["findings"] if "priority" in f]
        order = {"High": 0, "Medium": 1, "Low": 2}
        for i in range(len(priorities) - 1):
            assert order.get(priorities[i], 9) <= order.get(priorities[i + 1], 9)

    def test_no_title_creates_high_finding(self, thin_page):
        thin_page["title"] = ""
        thin_page["title_length"] = 0
        result = audit_seo(thin_page)
        title_findings = [f for f in result["findings"] if "title" in f["metric"].lower()]
        assert any(f["priority"] == "High" for f in title_findings)

    def test_no_h1_creates_finding(self, thin_page):
        result = audit_seo(thin_page)
        h1_findings = [f for f in result["findings"] if "h1" in f["metric"].lower()]
        assert len(h1_findings) > 0

    def test_missing_alt_images_creates_finding(self, thin_page):
        result = audit_seo(thin_page)
        img_findings = [f for f in result["findings"] if "alt" in f["metric"].lower() or "image" in f["metric"].lower()]
        assert len(img_findings) > 0

    def test_no_viewport_creates_finding(self, thin_page):
        result = audit_seo(thin_page)
        mobile_findings = [f for f in result["findings"]
                           if "mobile" in f["metric"].lower() or "viewport" in f["metric"].lower()]
        assert len(mobile_findings) > 0

    def test_score_is_float_between_0_and_100(self, sample_page, thin_page):
        for page in [sample_page, thin_page]:
            result = audit_seo(page)
            assert 0.0 <= result["overall_score"] <= 100.0

    def test_each_finding_has_required_fields(self, sample_page):
        result = audit_seo(sample_page)
        for finding in result["findings"]:
            for field in ["metric", "priority", "recommendation", "business_impact"]:
                assert field in finding, f"Finding missing '{field}': {finding}"


# ===========================================================================
# audit_sitewide
# ===========================================================================

class TestAuditSitewide:
    def test_empty_pages_returns_zero_score(self):
        result = audit_sitewide({"pages": []}, [])
        assert result["overall_score"] == 0.0

    def test_result_has_required_keys(self, sample_crawl_data):
        page_audits = [audit_seo(p) for p in sample_crawl_data["pages"]]
        result = audit_sitewide(sample_crawl_data, page_audits)
        for key in ["overall_score", "overall_seo_health", "findings",
                    "metric_summary", "category_scores", "page_summaries"]:
            assert key in result

    def test_category_scores_returned(self, sample_crawl_data):
        page_audits = [audit_seo(p) for p in sample_crawl_data["pages"]]
        result = audit_sitewide(sample_crawl_data, page_audits)
        cats = result["category_scores"]
        assert "metadata" in cats
        assert "content_depth" in cats

    def test_page_summaries_match_page_count(self, sample_crawl_data):
        page_audits = [audit_seo(p) for p in sample_crawl_data["pages"]]
        result = audit_sitewide(sample_crawl_data, page_audits)
        assert len(result["page_summaries"]) == len(sample_crawl_data["pages"])

    def test_broken_links_reflected_in_findings(self, sample_crawl_data):
        sample_crawl_data["broken_link_summary"] = {
            "checked_count": 10,
            "broken_count": 5,
            "broken_ratio": 50.0,
            "broken_links": [{"source_url": "https://example.com/", "target_url": "https://example.com/broken", "status_code": 404, "is_broken": True}],
        }
        page_audits = [audit_seo(p) for p in sample_crawl_data["pages"]]
        result = audit_sitewide(sample_crawl_data, page_audits)
        broken_findings = [f for f in result["findings"] if "broken" in f["metric"].lower()]
        assert len(broken_findings) > 0
        assert broken_findings[0]["priority"] in {"High", "Medium"}

    def test_page_speed_included_when_provided(self, sample_crawl_data):
        page_audits = [audit_seo(p) for p in sample_crawl_data["pages"]]
        speed = {"score": 45, "response_time": 2.8, "page_size_kb": 120, "status": "Slow"}
        result = audit_sitewide(sample_crawl_data, page_audits, page_speed_data=speed)
        speed_findings = [f for f in result["findings"] if "speed" in f["metric"].lower()]
        assert len(speed_findings) > 0


# ===========================================================================
# report_builder
# ===========================================================================

class TestBuildManagementSummary:
    @pytest.fixture
    def audit_result(self, sample_page):
        return audit_seo(sample_page)

    @pytest.fixture
    def comparison_result(self):
        return {
            "keyword_overlap_score": "65%",
            "content_gap_ratio": "35%",
            "market_opportunities": [
                {"keyword": "seo tools", "market_opportunity_score": 8, "priority": "High",
                 "relevance_to_business": "Direct fit.", "supporting_gap_ratio": "35%",
                 "business_impact": "Expand reach.", "recommendation": "Create content."}
            ],
        }

    @pytest.fixture
    def crawl_data(self):
        return {"analyzed_pages": 25, "sample_coverage_ratio": 85.0}

    def test_returns_all_keys(self, audit_result, comparison_result, crawl_data):
        result = build_management_summary(audit_result, comparison_result, {}, crawl_data)
        for key in ["board_verdict", "strongest_asset", "biggest_risk",
                    "growth_opportunity", "confidence_note"]:
            assert key in result

    def test_high_score_gives_strong_verdict(self, comparison_result, crawl_data):
        audit_result = {"overall_score": 90.0, "findings": [], "metric_summary": []}
        result = build_management_summary(audit_result, comparison_result, {}, crawl_data)
        assert "strong" in result["board_verdict"].lower()

    def test_low_score_gives_risk_verdict(self, comparison_result, crawl_data):
        audit_result = {"overall_score": 40.0, "findings": [], "metric_summary": []}
        result = build_management_summary(audit_result, comparison_result, {}, crawl_data)
        assert "risk" in result["board_verdict"].lower()


class TestBuildRecommendedRoadmap:
    def test_returns_three_phases(self):
        audit = {"findings": [
            {"priority": "High", "metric": "Title", "recommendation": "Fix titles", "business_impact": "Impact"},
            {"priority": "Medium", "metric": "Meta", "recommendation": "Fix meta", "business_impact": "Impact"},
        ]}
        comparison = {"market_opportunities": [{"keyword": "seo audit"}]}
        result = build_recommended_roadmap(audit, comparison)
        assert len(result) == 3

    def test_timelines_are_correct(self):
        audit = {"findings": []}
        comparison = {"market_opportunities": []}
        result = build_recommended_roadmap(audit, comparison)
        timelines = [phase["timeline"] for phase in result]
        assert "0-30 days" in timelines
        assert "31-60 days" in timelines
        assert "61-90 days" in timelines

    def test_each_phase_has_required_keys(self):
        audit = {"findings": []}
        comparison = {"market_opportunities": []}
        result = build_recommended_roadmap(audit, comparison)
        for phase in result:
            for key in ["timeline", "priority", "objective", "actions", "expected_outcome"]:
                assert key in phase


class TestBuildDataLimitations:
    def test_returns_5_limitations(self):
        result = build_data_limitations({"analyzed_pages": 25, "sample_coverage_ratio": 50.0})
        assert len(result) == 5

    def test_each_limitation_has_required_keys(self):
        result = build_data_limitations({"analyzed_pages": 10, "sample_coverage_ratio": 30.0})
        for item in result:
            for key in ["data_source", "current_status", "why_it_matters", "next_step"]:
                assert key in item
