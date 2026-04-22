from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class URLRequest(BaseModel):
    url: str


class FixRequest(BaseModel):
    issue: str


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


class PageSummary(BaseModel):
    url: str
    page_type: str
    title: str
    word_count: int
    seo_health: str
    key_issue: str
    canonical_url: str
    has_canonical: bool
    page_authority: int
    dofollow_links: int
    nofollow_links: int
    url_structure: URLStructure


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
    score: int
    response_time: float
    page_size_kb: float
    status: str


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
    backlink_strength: str
    estimated_backlinks: int
    referring_domains: int


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
