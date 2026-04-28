import logging

logger = logging.getLogger(__name__)

class SEOScoringEngine:
    """Encapsulates all SEO scoring logic into a modular engine."""
    
    WEIGHTS = {
        "technical": 0.25,
        "onpage": 0.20,
        "content": 0.20,
        "performance": 0.20,
        "issues": 0.15
    }

    def calculate_technical_score(self, page_data: dict) -> float:
        """Calculates Technical SEO score."""
        url = page_data.get("url", "")
        t_https = 100 if url.startswith("https") else 50
        t_mobile = 100 if page_data.get("has_viewport_meta", True) else 50
        t_broken = 100 if not page_data.get("crawl_issues") else 70
        return (t_https + t_mobile + t_broken) / 3

    def calculate_onpage_score(self, title: str, meta_desc: str, h1_count: int) -> float:
        """Calculates On-Page SEO score."""
        o_title = 100 if title != "N/A" and 10 < len(title) < 70 else 50
        o_meta = 100 if meta_desc != "Not Found" else 0
        o_h1 = 100 if h1_count == 1 else (50 if h1_count > 1 else 0)
        return (o_title + o_meta + o_h1) / 3

    def calculate_content_score(self, word_count: int) -> float:
        """Calculates Content Quality score."""
        if word_count < 300:
            return 40.0
        elif word_count <= 800:
            return 70.0
        else:
            return 100.0

    def calculate_performance_score(self, mob_score: int, desk_score: int) -> float:
        """Calculates Performance score."""
        return (mob_score + desk_score) / 2.0

    def calculate_issues_score(self, issues: dict) -> float:
        """Calculates Issues deduction score."""
        base_issues_score = 100 - (
            len(issues.get("critical", [])) * 15 +
            len(issues.get("high", [])) * 10 +
            len(issues.get("medium", [])) * 5 +
            len(issues.get("low", [])) * 2
        )
        return float(max(0, base_issues_score))

    def calculate_health(self, page_data: dict) -> dict:
        """Main entry point for calculating full SEO health for a single page."""
        try:
            tech = self.calculate_technical_score(page_data)
            onpage = self.calculate_onpage_score(
                page_data.get("title", "N/A"),
                page_data.get("meta_description", "Not Found"),
                page_data.get("h1_count", 0)
            )
            content = self.calculate_content_score(page_data.get("word_count", 0))
            perf = self.calculate_performance_score(
                page_data.get("mobile_score", 50),
                page_data.get("desktop_score", 50)
            )
            issue_score = self.calculate_issues_score(
                page_data.get("issues", {"critical": [], "high": [], "medium": [], "low": []})
            )

            # Apply weights
            seo_health = (
                tech * self.WEIGHTS["technical"] +
                onpage * self.WEIGHTS["onpage"] +
                content * self.WEIGHTS["content"] +
                perf * self.WEIGHTS["performance"] +
                issue_score * self.WEIGHTS["issues"]
            )
            
            final_score = int(max(1, min(100, round(seo_health))))
            
            return {
                "seo_score": final_score,
                "scores": {
                    "technical": int(tech),
                    "onpage": int(onpage),
                    "content": int(content),
                    "performance": int(perf),
                    "issues": int(issue_score)
                }
            }
        except Exception as e:
            logger.error(f"Error calculating SEO health: {e}")
            return {
                "seo_score": 1,
                "scores": {"technical": 0, "onpage": 0, "content": 0, "performance": 0, "issues": 0}
            }

def calculate_seo_health(page_data: dict) -> dict:
    """Compatibility wrapper for the new scoring engine."""
    engine = SEOScoringEngine()
    return engine.calculate_health(page_data)
