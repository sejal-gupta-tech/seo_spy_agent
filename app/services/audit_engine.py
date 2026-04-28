import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.core.config import SEO_BENCHMARKS
from app.utils.helpers import clamp, range_attainment, format_percentage, status_from_score

class BaseAuditor(ABC):
    """Base class for all SEO auditors."""
    
    @abstractmethod
    def audit(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

class MetadataAuditor(BaseAuditor):
    def audit(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        title = page_data.get("title", "")
        description = page_data.get("description", "")
        
        # Title Audit
        title_benchmark = SEO_BENCHMARKS["title_length"]
        title_len = len(title)
        title_score = range_attainment(title_len, title_benchmark["min"], title_benchmark["max"])
        
        # Description Audit
        desc_benchmark = SEO_BENCHMARKS["meta_description_length"]
        desc_len = len(description)
        desc_score = range_attainment(desc_len, desc_benchmark["min"], desc_benchmark["max"])
        
        return {
            "title_score": title_score,
            "description_score": desc_score,
            "metadata_health": (title_score + desc_score) / 2
        }

class ContentAuditor(BaseAuditor):
    def audit(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        word_count = page_data.get("word_count", 0)
        
        # Word Count Scoring
        if word_count < 300:
            score = 40
        elif word_count < 800:
            score = 70
        else:
            score = 100
            
        return {
            "word_count_score": score,
            "word_count": word_count,
            "quality": "Low" if score < 50 else "High"
        }

class TechnicalAuditor(BaseAuditor):
    def audit(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "https": page_data.get("url", "").startswith("https"),
            "mobile_friendly": page_data.get("has_viewport", True),
            "technical_score": 100 if page_data.get("url", "").startswith("https") else 50
        }

class AuditEngine:
    """Orchestrates multiple auditors to perform a full page audit."""
    
    def __init__(self):
        self.auditors = [
            MetadataAuditor(),
            ContentAuditor(),
            TechnicalAuditor()
        ]
        
    async def audit_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs all registered auditors on a single page."""
        results = {}
        for auditor in self.auditors:
            # We can use to_thread if auditors become CPU heavy
            audit_result = auditor.audit(page_data)
            results.update(audit_result)
        return results

    async def audit_site_concurrently(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Audits multiple pages in parallel to maximize performance."""
        tasks = [self.audit_page(page) for page in pages]
        return await asyncio.gather(*tasks)
