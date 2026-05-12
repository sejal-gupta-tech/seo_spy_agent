import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.core.config import SEO_BENCHMARKS
from app.core.logger import logger
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
        
        logger.debug(f"Starting metadata audit for page: title='{title[:50]}...', description='{description[:50]}...'")
        
        # Title Audit
        title_benchmark = SEO_BENCHMARKS["title_length"]
        title_len = len(title)
        title_score = range_attainment(title_len, title_benchmark["min"], title_benchmark["max"])
        
        # Description Audit
        desc_benchmark = SEO_BENCHMARKS["meta_description_length"]
        desc_len = len(description)
        desc_score = range_attainment(desc_len, desc_benchmark["min"], desc_benchmark["max"])
        
        result = {
            "title_score": title_score,
            "description_score": desc_score,
            "metadata_health": (title_score + desc_score) / 2
        }
        
        logger.debug(f"Metadata audit completed: title_score={title_score}, description_score={desc_score}, metadata_health={result['metadata_health']}")
        
        return result

class ContentAuditor(BaseAuditor):
    def audit(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        word_count = page_data.get("word_count", 0)
        
        logger.debug(f"Starting content audit: word_count={word_count}")
        
        # Word Count Scoring
        if word_count < 300:
            score = 40
        elif word_count < 800:
            score = 70
        else:
            score = 100
            
        result = {
            "word_count_score": score,
            "word_count": word_count,
            "quality": "Low" if score < 50 else "High"
        }
        
        logger.debug(f"Content audit completed: score={score}, quality={result['quality']}")
        
        return result

class TechnicalAuditor(BaseAuditor):
    def audit(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        url = page_data.get("url", "")
        
        logger.debug(f"Starting technical audit for URL: {url}")
        
        https = url.startswith("https")
        mobile_friendly = page_data.get("has_viewport", True)
        technical_score = 100 if https else 50
        
        result = {
            "https": https,
            "mobile_friendly": mobile_friendly,
            "technical_score": technical_score
        }
        
        logger.debug(f"Technical audit completed: https={https}, mobile_friendly={mobile_friendly}, technical_score={technical_score}")
        
        return result

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
        url = page_data.get("url", "unknown")
        logger.info(f"Starting audit for page: {url}")
        
        results = {}
        for auditor in self.auditors:
            # We can use to_thread if auditors become CPU heavy
            audit_result = auditor.audit(page_data)
            results.update(audit_result)
        
        logger.info(f"Audit completed for page: {url}, overall metadata_health={results.get('metadata_health', 'N/A')}")
        return results

    async def audit_site_concurrently(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Audits multiple pages in parallel to maximize performance."""
        num_pages = len(pages)
        logger.info(f"Starting concurrent audit for {num_pages} pages")
        
        tasks = [self.audit_page(page) for page in pages]
        results = await asyncio.gather(*tasks)
        
        logger.info(f"Concurrent audit completed for {num_pages} pages")
        return results
