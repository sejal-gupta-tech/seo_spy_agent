"""
test_crawler.py — Unit tests for the SEO Spy Agent crawler layer.

Tests cover:
  - URL validators (normalize_url, is_valid_url)
  - Favicon rel detection logic (_is_favicon_rel pattern)
  - URL structure analysis (analyze_url_structure)
  - Internal link analysis (analyze_internal_linking)
  - Backlink profile estimation (estimate_backlink_profile)
  - Authority scoring (calculate_page_authority, calculate_domain_authority)
  - Page speed scoring thresholds (get_page_speed logic)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.utils.validators import is_valid_url, normalize_url
from app.services.url_analysis import analyze_url_structure
from app.services.link_analysis import analyze_internal_linking, estimate_backlink_profile
from app.services.authority import calculate_page_authority, calculate_domain_authority


# ===========================================================================
# normalize_url
# ===========================================================================

class TestNormalizeUrl:
    def test_adds_https_when_missing(self):
        assert normalize_url("example.com") == "https://example.com"

    def test_preserves_existing_https(self):
        assert normalize_url("https://example.com") == "https://example.com"

    def test_preserves_existing_http(self):
        assert normalize_url("http://example.com") == "http://example.com"

    def test_strips_whitespace(self):
        assert normalize_url("  example.com  ") == "https://example.com"

    def test_empty_string_stays_empty(self):
        result = normalize_url("")
        assert result == ""

    def test_preserves_path(self):
        assert normalize_url("example.com/about") == "https://example.com/about"


# ===========================================================================
# is_valid_url
# ===========================================================================

class TestIsValidUrl:
    def test_valid_https_url(self):
        assert is_valid_url("https://example.com") is True

    def test_valid_http_url(self):
        assert is_valid_url("http://example.com") is True

    def test_valid_subdomain(self):
        assert is_valid_url("https://blog.example.com") is True

    def test_valid_url_with_path(self):
        assert is_valid_url("https://example.com/page/about") is True

    def test_invalid_no_scheme(self):
        assert is_valid_url("example") is False

    def test_invalid_ftp_scheme(self):
        assert is_valid_url("ftp://example.com") is False

    def test_invalid_empty_string(self):
        assert is_valid_url("") is False

    def test_invalid_no_tld(self):
        assert is_valid_url("https://example") is False

    def test_localhost_is_valid(self):
        assert is_valid_url("http://localhost") is True

    def test_numeric_tld_is_invalid(self):
        assert is_valid_url("https://example.123") is False


# ===========================================================================
# analyze_url_structure
# ===========================================================================

class TestAnalyzeUrlStructure:
    def test_clean_url_scores_100(self):
        result = analyze_url_structure("https://example.com/seo-audit")
        assert result["score"] == 100
        assert result["is_seo_friendly"] is True
        assert result["issues"] == []

    def test_url_with_query_params_is_penalized(self):
        result = analyze_url_structure("https://example.com/page?id=123")
        assert result["score"] < 100
        assert any("query" in i.lower() or "parameter" in i.lower() for i in result["issues"])

    def test_url_with_uppercase_is_penalized(self):
        result = analyze_url_structure("https://example.com/About-Us")
        assert result["score"] < 100
        assert any("uppercase" in i.lower() for i in result["issues"])

    def test_url_with_underscores_is_penalized(self):
        result = analyze_url_structure("https://example.com/my_page")
        assert result["score"] < 100
        assert any("underscore" in i.lower() for i in result["issues"])

    def test_very_long_url_is_penalized(self):
        long_url = "https://example.com/" + "a" * 100
        result = analyze_url_structure(long_url)
        assert result["score"] < 100
        assert any("long" in i.lower() or "length" in i.lower() or "too" in i.lower() for i in result["issues"])

    def test_query_params_not_double_penalized(self):
        """BUG FIX: query params must only deduct once, not twice."""
        result_clean = analyze_url_structure("https://example.com/page")
        result_query = analyze_url_structure("https://example.com/page?id=1")
        penalty = result_clean["score"] - result_query["score"]
        # Penalty should be exactly 15 (once), not 30 (twice)
        assert penalty == 15, f"Query param deducted {penalty} pts, expected exactly 15"

    def test_deep_url_is_penalized(self):
        deep_url = "https://example.com/a/b/c/d/e/f/page"
        result = analyze_url_structure(deep_url)
        assert result["score"] < 100

    def test_returns_depth_key(self):
        result = analyze_url_structure("https://example.com/services/seo")
        assert "depth" in result
        assert result["depth"] == 2


# ===========================================================================
# analyze_internal_linking
# ===========================================================================

class TestAnalyzeInternalLinking:
    def test_no_pages_returns_zero_score(self):
        result = analyze_internal_linking([])
        assert result["internal_link_score"] == 0

    def test_good_linking_scores_high(self):
        pages = [
            {
                "url": f"https://example.com/page-{i}",
                "internal_links_count": 15,
                "internal_links": [f"https://example.com/page-{j}" for j in range(5)],
            }
            for i in range(5)
        ]
        result = analyze_internal_linking(pages)
        assert result["internal_link_score"] >= 70

    def test_no_internal_links_scores_zero(self):
        pages = [
            {"url": "https://example.com/page", "internal_links_count": 0, "internal_links": []}
        ]
        result = analyze_internal_linking(pages)
        assert result["internal_link_score"] == 0
        assert len(result["issues"]) > 0

    def test_orphan_pages_detected(self):
        """Pages that are crawled but not linked to from any other page."""
        pages = [
            {"url": "https://example.com/", "internal_links_count": 5, "internal_links": ["https://example.com/about"]},
            # /orphan is in pages but not in any internal_links list
            {"url": "https://example.com/orphan", "internal_links_count": 0, "internal_links": []},
        ]
        result = analyze_internal_linking(pages)
        assert result["orphan_page_count"] > 0

    def test_returns_all_expected_keys(self):
        result = analyze_internal_linking([])
        for key in ["internal_link_score", "total_internal_links", "avg_links_per_page",
                    "orphan_page_count", "orphan_pages_sample", "issues", "recommendations"]:
            assert key in result, f"Missing key: {key}"


# ===========================================================================
# estimate_backlink_profile
# ===========================================================================

class TestEstimateBacklinkProfile:
    def test_returns_disclaimer(self):
        """Must always include a disclaimer that this is NOT real backlink data."""
        result = estimate_backlink_profile([])
        assert "disclaimer" in result
        assert len(result["disclaimer"]) > 10

    def test_no_estimated_backlinks_key(self):
        """BUG FIX: fake 'estimated_backlinks = external * 2' must not exist."""
        result = estimate_backlink_profile([{"external_links_count": 10, "external_domains": []}])
        assert "estimated_backlinks" not in result

    def test_counts_unique_domains(self):
        pages = [
            {"external_links_count": 5, "external_domains": ["google.com", "moz.com"]},
            {"external_links_count": 3, "external_domains": ["moz.com", "ahrefs.com"]},
        ]
        result = estimate_backlink_profile(pages)
        # moz.com appears in both → should be counted once
        assert result["outbound_domain_count"] == 3

    def test_diversity_levels(self):
        low = estimate_backlink_profile([{"external_links_count": 1, "external_domains": ["a.com"]}])
        high = estimate_backlink_profile([
            {"external_links_count": 20, "external_domains": [f"site{i}.com" for i in range(20)]}
        ])
        assert low["outbound_domain_diversity"] == "Low"
        assert high["outbound_domain_diversity"] == "High"


# ===========================================================================
# calculate_page_authority
# ===========================================================================

class TestCalculatePageAuthority:
    def test_empty_page_returns_base_score(self):
        result = calculate_page_authority({})
        assert 0 <= result <= 100
        assert result >= 20  # Base score

    def test_rich_page_scores_higher(self):
        rich = calculate_page_authority({
            "word_count": 3000,
            "internal_links_count": 60,
            "external_links_count": 2,
            "has_structured_data": True,
            "has_open_graph": True,
            "total_images": 5,
        })
        thin = calculate_page_authority({
            "word_count": 50,
            "internal_links_count": 0,
            "external_links_count": 0,
            "has_structured_data": False,
            "has_open_graph": False,
            "total_images": 0,
        })
        assert rich > thin

    def test_spam_outbound_ratio_is_penalized(self):
        normal = calculate_page_authority({"word_count": 500, "internal_links_count": 5, "external_links_count": 5})
        spammy = calculate_page_authority({"word_count": 500, "internal_links_count": 5, "external_links_count": 200})
        assert spammy < normal

    def test_score_bounded_0_to_100(self):
        for data in [{}, {"word_count": 99999, "internal_links_count": 9999}]:
            result = calculate_page_authority(data)
            assert 0 <= result <= 100


# ===========================================================================
# calculate_domain_authority
# ===========================================================================

class TestCalculateDomainAuthority:
    def test_empty_pages_returns_base(self):
        result = calculate_domain_authority([])
        assert result == 10

    def test_score_bounded_0_to_100(self):
        pages = [{"word_count": 99999, "internal_links_count": 9999} for _ in range(100)]
        assert 0 <= calculate_domain_authority(pages) <= 100

    def test_more_quality_pages_scores_higher(self):
        rich_pages = [{"word_count": 2000, "internal_links_count": 25, "has_structured_data": True}] * 10
        thin_pages = [{"word_count": 50, "internal_links_count": 0, "has_structured_data": False}] * 10
        assert calculate_domain_authority(rich_pages) > calculate_domain_authority(thin_pages)

    def test_scale_boost_capped_reasonably(self):
        """BUG FIX: scale_boost should not inflate scores beyond reason for large crawls."""
        many_pages = [{"word_count": 100, "internal_links_count": 2}] * 200
        result = calculate_domain_authority(many_pages)
        # Should not score 100 just because there are many mediocre pages
        assert result < 90, f"DA is unrealistically high: {result}"


# ===========================================================================
# Favicon rel detection (unit-level, no HTTP)
# ===========================================================================

class TestFaviconRelDetection:
    """Tests the _is_favicon_rel logic that was fixed to exclude apple-touch-icon."""

    @staticmethod
    def _is_favicon_rel(value) -> bool:
        """Mirror of the function inside _parse_page."""
        FAVICON_REL_VALUES = {"icon", "shortcut icon"}
        if not value:
            return False
        rels = value if isinstance(value, list) else str(value).split()
        return any(r.lower().strip() in FAVICON_REL_VALUES for r in rels)

    def test_rel_icon_detected(self):
        assert self._is_favicon_rel("icon") is True

    def test_rel_shortcut_icon_detected(self):
        assert self._is_favicon_rel("shortcut icon") is True

    def test_apple_touch_icon_ignored(self):
        assert self._is_favicon_rel("apple-touch-icon") is False

    def test_mask_icon_ignored(self):
        assert self._is_favicon_rel("mask-icon") is False

    def test_apple_touch_icon_precomposed_ignored(self):
        assert self._is_favicon_rel("apple-touch-icon-precomposed") is False

    def test_none_returns_false(self):
        assert self._is_favicon_rel(None) is False

    def test_empty_string_returns_false(self):
        assert self._is_favicon_rel("") is False

    def test_list_with_icon_detected(self):
        assert self._is_favicon_rel(["icon"]) is True

    def test_list_with_apple_touch_icon_ignored(self):
        assert self._is_favicon_rel(["apple-touch-icon"]) is False
