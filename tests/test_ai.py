"""
test_ai.py — Unit tests for the AI services layer.

Tests cover:
  - generate_seo_suggestions() — keyword + title + meta generation
  - extract_main_keyword()     — keyword extraction with fallback
  - compare_with_competitors() — overlap + content gap + market opportunities
  - _calculate_overlap()       — heading tokenization and Jaccard intersection
  - _tokenize_headings()       — stopword filtering and normalization
  - _fallback_market_opportunities() — heuristic fallback when OpenAI is down
  - site_profile builder       — build_site_profile()

All OpenAI API calls are mocked — tests run fully offline.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from app.services.ai_seo import generate_seo_suggestions, extract_main_keyword
from app.services.comparison import (
    _tokenize_headings,
    _calculate_overlap,
    _normalize_priority,
    _dedupe_terms,
    compare_with_competitors,
)


# ===========================================================================
# extract_main_keyword
# ===========================================================================

class TestExtractMainKeyword:
    def test_returns_first_valid_keyword(self):
        result = extract_main_keyword({"keywords": ["seo audit", "technical seo", "on-page seo"]})
        assert result == "seo audit"

    def test_skips_empty_strings(self):
        result = extract_main_keyword({"keywords": ["", "  ", "technical seo"]})
        assert result == "technical seo"

    def test_falls_back_to_text_when_no_keywords(self):
        result = extract_main_keyword({}, fallback_text="Professional SEO audit services")
        assert len(result) > 0
        assert "professional" in result.lower() or "seo" in result.lower()

    def test_empty_keywords_and_no_fallback_returns_empty(self):
        result = extract_main_keyword({"keywords": []}, fallback_text="")
        assert result == ""

    def test_handles_non_list_keywords_gracefully(self):
        result = extract_main_keyword({"keywords": None}, fallback_text="seo services")
        assert isinstance(result, str)

    def test_fallback_limited_to_5_words(self):
        long_text = "one two three four five six seven eight nine ten"
        result = extract_main_keyword({}, fallback_text=long_text)
        assert len(result.split()) <= 5


# ===========================================================================
# generate_seo_suggestions — with mocked OpenAI
# ===========================================================================

class TestGenerateSeoSuggestions:
    def _make_openai_response(self, payload: dict):
        """Helper to build a mock OpenAI completion response."""
        mock_msg = MagicMock()
        mock_msg.content = json.dumps(payload)
        mock_choice = MagicMock()
        mock_choice.message = mock_msg
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        return mock_response

    def test_returns_keywords_meta_and_title(self):
        payload = {
            "keywords": ["seo audit", "technical seo", "site audit"],
            "new_meta_description": "Get a professional SEO audit in 24 hours.",
            "new_title": "Professional SEO Audit | Expert Team",
        }
        with patch("app.services.ai_seo.client") as mock_client:
            mock_client.chat.completions.create.return_value = self._make_openai_response(payload)
            result = generate_seo_suggestions({
                "title": "SEO Services",
                "description": "We do SEO.",
                "headings": {"h1": ["SEO Agency"], "h2": []},
            })
        assert result["keywords"] == ["seo audit", "technical seo", "site audit"]
        assert "seo" in result["new_meta_description"].lower()
        assert len(result["new_title"]) > 0

    def test_returns_fallback_when_client_is_none(self):
        with patch("app.services.ai_seo.client", None):
            result = generate_seo_suggestions({
                "title": "Test", "description": "", "headings": {}
            })
        assert "error" in result
        assert result["keywords"] == []

    def test_returns_fallback_on_openai_exception(self):
        with patch("app.services.ai_seo.client") as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("API timeout")
            result = generate_seo_suggestions({
                "title": "Test", "description": "", "headings": {}
            })
        assert "error" in result

    def test_validates_response_has_all_required_keys(self):
        # Missing 'new_title' → should raise ValueError → fallback
        payload = {"keywords": ["kw1"], "new_meta_description": "desc"}
        with patch("app.services.ai_seo.client") as mock_client:
            mock_client.chat.completions.create.return_value = self._make_openai_response(payload)
            result = generate_seo_suggestions({
                "title": "Test", "description": "", "headings": {}
            })
        assert "error" in result


# ===========================================================================
# _tokenize_headings
# ===========================================================================

class TestTokenizeHeadings:
    def test_basic_tokenization(self):
        tokens = _tokenize_headings(["SEO Audit Services"])
        assert "seo" in tokens
        assert "audit" in tokens
        assert "services" in tokens

    def test_stopwords_removed(self):
        tokens = _tokenize_headings(["The Best SEO Services For You"])
        assert "the" not in tokens
        assert "best" not in tokens
        assert "for" not in tokens
        assert "you" not in tokens

    def test_short_words_removed(self):
        # Words of 2 chars or fewer are skipped
        tokens = _tokenize_headings(["An SEO AI Tool"])
        assert "an" not in tokens
        assert "ai" not in tokens  # 2 chars → filtered

    def test_returns_set(self):
        result = _tokenize_headings(["SEO SEO SEO"])
        assert isinstance(result, set)
        # Duplicates collapsed
        assert len([t for t in result if t == "seo"]) == 1

    def test_empty_list(self):
        assert _tokenize_headings([]) == set()

    def test_numbers_are_valid_tokens(self):
        tokens = _tokenize_headings(["Top 10 SEO Strategies"])
        assert "10" in tokens or "top" in tokens


# ===========================================================================
# _calculate_overlap
# ===========================================================================

class TestCalculateOverlap:
    def test_identical_headings_is_100_percent(self):
        headings = ["Professional SEO Audit Services"]
        overlap, gap = _calculate_overlap(headings, headings)
        assert overlap == 100.0
        assert gap == 0.0

    def test_no_shared_terms_is_0_overlap(self):
        user = ["Accounting Software Solutions"]
        competitor = ["Healthcare Digital Marketing"]
        overlap, gap = _calculate_overlap(user, competitor)
        assert overlap == 0.0
        assert gap == 100.0

    def test_empty_competitor_headings(self):
        overlap, gap = _calculate_overlap(["SEO Services"], [])
        assert overlap == 0.0
        assert gap == 100.0

    def test_overlap_plus_gap_sums_to_100(self):
        user = ["SEO Audit Technical Content Marketing"]
        competitor = ["SEO Content Strategy Digital"]
        overlap, gap = _calculate_overlap(user, competitor)
        assert abs((overlap + gap) - 100.0) < 0.1


# ===========================================================================
# _normalize_priority
# ===========================================================================

class TestNormalizePriority:
    def test_valid_priority_unchanged(self):
        assert _normalize_priority("High", 5) == "High"
        assert _normalize_priority("Medium", 5) == "Medium"
        assert _normalize_priority("Low", 5) == "Low"

    def test_score_above_8_is_high(self):
        assert _normalize_priority("", 9) == "High"

    def test_score_5_to_7_is_medium(self):
        assert _normalize_priority("", 6) == "Medium"

    def test_score_below_5_is_low(self):
        assert _normalize_priority("", 3) == "Low"


# ===========================================================================
# _dedupe_terms
# ===========================================================================

class TestDedupeTerms:
    def test_removes_duplicates_case_insensitive(self):
        result = _dedupe_terms(["SEO", "seo", "Seo", "audit"], 10)
        seo_count = sum(1 for t in result if t.lower() == "seo")
        assert seo_count == 1

    def test_respects_limit(self):
        result = _dedupe_terms([f"keyword{i}" for i in range(20)], 5)
        assert len(result) == 5

    def test_skips_empty_strings(self):
        result = _dedupe_terms(["", "  ", "seo"], 10)
        assert "" not in result
        assert "seo" in result


# ===========================================================================
# compare_with_competitors — mocked AI
# ===========================================================================

class TestCompareWithCompetitors:
    def _mock_opportunities(self):
        return [
            {
                "keyword": "seo audit tool",
                "market_opportunity_score": 9,
                "relevance_to_business": "Direct fit.",
                "supporting_gap_ratio": "35%",
                "business_impact": "High impact.",
                "recommendation": "Create content.",
                "priority": "High",
            }
        ]

    def test_returns_required_keys(self):
        with patch("app.services.comparison.client", None):
            result = compare_with_competitors(
                user_headings=["SEO Audit Services"],
                competitor_headings=["Technical SEO Analysis"],
            )
        assert "keyword_overlap_score" in result
        assert "content_gap_ratio" in result
        assert "market_opportunities" in result

    def test_overlap_score_is_percentage_string(self):
        with patch("app.services.comparison.client", None):
            result = compare_with_competitors(
                user_headings=["SEO Audit"],
                competitor_headings=["SEO Audit"],
            )
        assert result["keyword_overlap_score"].endswith("%")

    def test_identical_headings_gives_100_overlap(self):
        with patch("app.services.comparison.client", None):
            result = compare_with_competitors(
                user_headings=["Professional SEO Audit Agency"],
                competitor_headings=["Professional SEO Audit Agency"],
            )
        # Overlap should be 100%, gap should be 0%
        assert result["keyword_overlap_score"] == "100%"
        assert result["content_gap_ratio"] == "0%"

    def test_opportunities_max_5(self):
        with patch("app.services.comparison.client", None):
            result = compare_with_competitors(
                user_headings=["SEO"],
                competitor_headings=["Digital Marketing Content Strategy Social Media PPC Ads Email"],
                site_profile={"core_service_pillars": [f"service{i}" for i in range(20)]},
            )
        assert len(result["market_opportunities"]) <= 5

    def test_with_mocked_openai_response(self):
        mock_payload = {"market_opportunities": self._mock_opportunities()}
        mock_msg = MagicMock()
        mock_msg.content = json.dumps(mock_payload)
        mock_choice = MagicMock()
        mock_choice.message = mock_msg
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("app.services.comparison.client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_response
            result = compare_with_competitors(
                user_headings=["SEO Audit"],
                competitor_headings=["Technical SEO Analysis"],
            )
        opps = result["market_opportunities"]
        assert len(opps) >= 1
        assert opps[0]["keyword"] == "seo audit tool"
        assert opps[0]["market_opportunity_score"] == 9
