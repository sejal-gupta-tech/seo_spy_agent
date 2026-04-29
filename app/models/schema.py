from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class URLRequest(BaseModel):
    url: str
    business_type: Optional[str] = "General"


class FixRequest(BaseModel):
    issue: str = Field(..., alias="finding", validation_alias="finding")

    model_config = {
        "populate_by_name": True
    }


class FixResponse(BaseModel):
    issue: str
    current_code: str
    fixed_code: str
    explanation: str


class EvidencePoint(BaseModel):
    url: str
    observation: str


class MetricSnapshot(BaseModel):
    metric: str
    current_value: str
    benchmark: str
    status: str


class TechnicalFinding(BaseModel):
    category: str
    metric: str
    current_value: str
    benchmark: str
    status: str
    business_impact: str
    recommendation: str
    priority: Literal["High", "Medium", "Low"]
    evidence: List[EvidencePoint] = Field(default_factory=list)
    score: float = 100.0


class ScoreBreakdownItem(BaseModel):
    module: str
    score: float
    impact: str
    reason: str


class MarketOpportunity(BaseModel):
    keyword: str
    market_opportunity_score: int
    relevance_to_business: str
    supporting_gap_ratio: str
    business_impact: str
    recommendation: str
    priority: Literal["High", "Medium", "Low"]


class URLStructure(BaseModel):
    is_seo_friendly: bool
    issues: List[str]
    recommendations: List[str]
    score: int


class PageInfo(BaseModel):
    title: str = "N/A"
    meta_description: str = "Not Found"
    canonical: str = "Not Found"
    indexing_status: str = "Unknown"

class PerformanceItem(BaseModel):
    score: int = 0
    load_time: str = "0s"
    status: str = "N/A"

class SiteFavicon(BaseModel):
    status: str
    url: str
    source: str

class PagePerformance(BaseModel):
    mobile: PerformanceItem
    desktop: PerformanceItem
    issues: List[str] = []

class PageHeadings(BaseModel):
    h1_count: int = 0
    h1_content: str = "Missing"
    h2_count: int = 0
    h3_count: int = 0
    warnings: List[str] = []

class PageContent(BaseModel):
    word_count: int = 0
    quality: str = "N/A"
    keyword_gaps: List[str] = []

class TechnicalSEO(BaseModel):
    mobile_friendly: bool = True
    https: bool = True
    broken_links: List[str] = []
    crawl_issues: List[str] = []

class InternalLinking(BaseModel):
    dofollow_links: int = 0
    nofollow_links: int = 0

class Backlinks(BaseModel):
    page_authority: int = 0

class PageSummary(BaseModel):
    model_config = {"extra": "allow"}
    
    url: str
    page_info: PageInfo
    performance: PagePerformance
    headings: PageHeadings
    content: PageContent
    technical_seo: TechnicalSEO
    internal_linking: InternalLinking
    backlinks: Backlinks
    seo_score: int = 0
    scores: Optional[Dict[str, int]] = None
    issues: Dict[str, List[str]] = Field(default_factory=lambda: {"critical": [], "high": [], "medium": [], "low": []})
    recommendations: List[str] = []
    priority_action: str = "None"



class CrawlOverview(BaseModel):
    analyzed_pages: int
    discovered_internal_pages: int
    sample_coverage_ratio: str
    crawl_depth: int
    robots_txt_status: str
    sitemap_status: str
    favicon_status: str
    domain_authority: int
    broken_internal_link_ratio: str
    sampled_pages: List[PageSummary]


class TechnicalAudit(BaseModel):
    benchmark_reference_year: int
    overall_seo_health: str
    metric_summary: List[MetricSnapshot]
    findings: List[TechnicalFinding]
    score_breakdown: List[ScoreBreakdownItem] = Field(default_factory=list)


class ManagementSummary(BaseModel):
    board_verdict: str
    strongest_asset: str
    biggest_risk: str
    growth_opportunity: str
    confidence_note: str


class CompetitiveIntelligence(BaseModel):
    keyword_overlap_score: str
    content_gap_ratio: str
    competitor_sample_size: int
    market_opportunities: List[MarketOpportunity]


class DataLimitation(BaseModel):
    data_source: str
    current_status: str
    why_it_matters: str
    next_step: str


class RoadmapItem(BaseModel):
    timeline: Literal["0-30 days", "31-60 days", "61-90 days"]
    priority: Literal["High", "Medium", "Low"]
    objective: str
    actions: List[str]
    expected_outcome: str


class DetailedAppendix(BaseModel):
    primary_page_url: str
    primary_page_audit: TechnicalAudit
    page_summaries: List[PageSummary]
    evidence_notes: List[str]


class PDFMetric(BaseModel):
    label: str
    value: str


class PDFPriorityAction(BaseModel):
    priority: Literal["High", "Medium", "Low"]
    headline: str
    action: str
    business_impact: str


class PDFTemplateData(BaseModel):
    report_title: str
    prepared_for: str
    website: str
    generated_on: str
    executive_summary: str
    board_verdict: str
    management_summary: ManagementSummary
    hero_metrics: List[PDFMetric]
    crawl_overview: List[PDFMetric]
    priority_actions: List[PDFPriorityAction]
    market_opportunities: List[MarketOpportunity]
    technical_findings: List[TechnicalFinding]
    metric_summary: List[MetricSnapshot]
    recommended_roadmap: List[RoadmapItem]
    content_strategy: ContentStrategy
    keyword_analysis: KeywordAnalysis
    page_speed: PageSpeedData
    link_analysis: LinkAnalysis
    ai_insights: List[AIInsightItem]
    sampled_pages: List[PageSummary]
    competitor_sample_size: int
    site_favicon: Optional[SiteFavicon] = None
    keyword_overlap_score: str
    content_gap_ratio: str
    data_limitations: List[DataLimitation]
    company_name: str
    business_summary: str


class BlogPost(BaseModel):
    title: str
    target_audience: str
    search_intent: str
    outline: List[str]


class ContentStrategy(BaseModel):
    blog_suggestions: List[BlogPost]
    guest_post_titles: List[str]


class PageSpeedData(BaseModel):
    score: int = 0
    response_time: float = 0.0
    page_size_kb: float = 0.0
    status: str = "N/A"
    mobile: Optional[PerformanceItem] = None
    desktop: Optional[PerformanceItem] = None


class KeywordIntent(BaseModel):
    informational: List[str]
    transactional: List[str]
    navigational: List[str]


class KeywordAnalysis(BaseModel):
    primary_keywords: List[str]
    long_tail_keywords: List[str]
    keyword_intent: KeywordIntent


class InternalLinkReport(BaseModel):
    internal_link_score: int
    issues: List[str]
    recommendations: List[str]


class ExternalLinkReport(BaseModel):
    total_external_links: int
    domains: List[str]


class BacklinkReport(BaseModel):
    backlink_strength: Optional[str] = "Unknown"
    estimated_backlinks: Optional[int] = 0
    referring_domains: Optional[int] = 0


class LinkAnalysis(BaseModel):
    internal: InternalLinkReport
    external: ExternalLinkReport
    backlinks: BacklinkReport


class AIInsightItem(BaseModel):
    issue: str
    impact: str
    priority: str
    explanation: str
    recommendation: str


class AIInsights(BaseModel):
    insights: List[AIInsightItem]


class FinalResponse(BaseModel):
    url: str
    overall_score: Optional[float] = 0.0
    seo_health: Optional[str] = "0%"
    site_favicon: Optional[SiteFavicon] = None
    site_profile: Optional[Dict[str, Any]] = None
    executive_summary: str
    management_summary: ManagementSummary
    crawl_overview: CrawlOverview
    technical_audit: TechnicalAudit
    competitive_intelligence: CompetitiveIntelligence
    data_limitations: List[DataLimitation]
    recommended_roadmap: List[RoadmapItem]
    detailed_appendix: DetailedAppendix
    pdf_template_data: PDFTemplateData
    content_strategy: ContentStrategy
    page_speed: PageSpeedData
    keyword_analysis: KeywordAnalysis
    link_analysis: LinkAnalysis
    ai_insights: AIInsights
    report_url: Optional[str] = None
    status: Optional[str] = "completed"


class AnalysisJobAccepted(BaseModel):
    job_id: str
    url: str
    status: Literal["queued", "running", "completed", "failed"]
    created_at: str
    status_url: str


class AnalysisJobStatus(BaseModel):
    job_id: str
    url: str
    status: Literal["queued", "running", "completed", "failed"]
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None
    latest_event: Optional[dict[str, Any]] = None
    recent_events: List[dict[str, Any]] = Field(default_factory=list)
    result: Optional[FinalResponse] = None
