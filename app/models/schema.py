from typing import List, Literal

from pydantic import BaseModel, Field


class URLRequest(BaseModel):
    url: str


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


class PageSummary(BaseModel):
    url: str
    page_type: str
    title: str
    word_count: int
    seo_health: str
    key_issue: str


class CrawlOverview(BaseModel):
    analyzed_pages: int
    discovered_internal_pages: int
    sample_coverage_ratio: str
    crawl_depth: int
    robots_txt_status: str
    sitemap_status: str
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
    hero_metrics: List[PDFMetric]
    crawl_overview: List[PDFMetric]
    priority_actions: List[PDFPriorityAction]
    market_opportunities: List[MarketOpportunity]
    data_limitations: List[DataLimitation]
    company_name: str
    business_summary: str


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
