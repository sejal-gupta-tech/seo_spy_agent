from datetime import date

from app.core.config import DEFAULT_COMPANY_NAME, DEFAULT_REPORT_AUDIENCE


def _safe_company_name(site_profile: dict) -> str:
    return site_profile.get("company_name") or DEFAULT_COMPANY_NAME


def _top_finding(findings: list[dict], priority: str | None = None) -> dict:
    for finding in findings:
        if priority is None or finding.get("priority") == priority:
            return finding
    return findings[0] if findings else {}


def _best_snapshot(metric_summary: list[dict]) -> dict:
    for snapshot in metric_summary:
        if snapshot.get("status") == "At Benchmark":
            return snapshot
    return metric_summary[0] if metric_summary else {}


def build_data_limitations(crawl_data: dict) -> list[dict]:
    analyzed_pages = crawl_data.get("analyzed_pages", 0)
    sample_coverage_ratio = crawl_data.get("sample_coverage_ratio", 0.0)

    return [
        {
            "data_source": "Google Search Console",
            "current_status": "Not connected",
            "why_it_matters": (
                "Search Console is required to validate impressions, clicks, CTR, index coverage, and query-level winners and losers."
            ),
            "next_step": (
                "Connect Search Console to layer live demand and indexation evidence onto this crawl-based audit."
            ),
        },
        {
            "data_source": "Analytics and Conversion Data",
            "current_status": "Not connected",
            "why_it_matters": (
                "Without GA4 or CRM data, the report cannot prove which pages generate leads, revenue, or assisted conversions."
            ),
            "next_step": (
                "Connect GA4 or downstream conversion reporting so SEO recommendations can be prioritized by revenue contribution."
            ),
        },
        {
            "data_source": "Core Web Vitals and Speed Testing",
            "current_status": "Not measured in this crawl",
            "why_it_matters": (
                "Page speed and Core Web Vitals directly affect user experience, mobile retention, and ranking stability."
            ),
            "next_step": (
                "Run PageSpeed Insights or field-data checks for key templates and merge the results into the final board pack."
            ),
        },
        {
            "data_source": "Backlink and Authority Intelligence",
            "current_status": "Not connected",
            "why_it_matters": (
                "Off-page authority determines how competitive the site can be against stronger domains, especially on high-intent queries."
            ),
            "next_step": (
                "Add backlink data from a third-party SEO platform to benchmark authority, referring domains, and link-gap opportunities."
            ),
        },
        {
            "data_source": "Full Site Crawl Coverage",
            "current_status": (
                f"Sample-based crawl completed across {analyzed_pages} pages with {sample_coverage_ratio}% coverage of discovered internal URLs."
            ),
            "why_it_matters": (
                "Sampled crawls are directionally strong, but template-level defects can still hide outside the sampled page set."
            ),
            "next_step": (
                "Run a full crawl for enterprise-grade assurance before using the report as the final source of truth for large sites."
            ),
        },
    ]


def build_management_summary(
    audit_result: dict,
    comparison_result: dict,
    site_profile: dict,
    crawl_data: dict,
) -> dict:
    overall_score = audit_result.get("overall_score", 0.0)
    findings = audit_result.get("findings", [])
    metric_summary = audit_result.get("metric_summary", [])
    opportunities = comparison_result.get("market_opportunities", [])
    best_snapshot = _best_snapshot(metric_summary)
    biggest_risk_finding = _top_finding(findings, "High")
    top_opportunity = opportunities[0] if opportunities else {}

    if overall_score >= 85:
        board_verdict = "Strong SEO foundation with scalable growth headroom."
    elif overall_score >= 70:
        board_verdict = "Moderate SEO maturity with clear operational gaps to close."
    else:
        board_verdict = "SEO performance is at risk and requires structured remediation."

    strongest_asset = (
        f"{best_snapshot.get('metric', 'Baseline coverage')} is the strongest visible asset, currently at {best_snapshot.get('current_value', 'benchmark level')}."
    )
    biggest_risk = (
        f"{biggest_risk_finding.get('metric', 'Technical discipline')} is the biggest current risk because {biggest_risk_finding.get('business_impact', 'site visibility is being constrained.').lower()}"
    )
    growth_opportunity = (
        f"Priority growth opportunity: expand coverage around {top_opportunity.get('keyword', 'high-intent topics')} to reduce the remaining {comparison_result.get('content_gap_ratio', '0%')} market gap."
    )
    confidence_note = (
        f"Medium confidence: this assessment is grounded in a live crawl of {crawl_data.get('analyzed_pages', 0)} sampled pages, but performance, analytics, and backlink systems were not connected."
    )

    return {
        "board_verdict": board_verdict,
        "strongest_asset": strongest_asset,
        "biggest_risk": biggest_risk,
        "growth_opportunity": growth_opportunity,
        "confidence_note": confidence_note,
    }


def build_executive_summary(
    audit_result: dict,
    comparison_result: dict,
    site_profile: dict,
    management_summary: dict,
) -> str:
    company_name = _safe_company_name(site_profile)
    overall_health = audit_result.get("overall_seo_health", "0%")
    content_gap_ratio = comparison_result.get("content_gap_ratio", "0%")
    opportunities = comparison_result.get("market_opportunities", [])
    top_opportunity = opportunities[0].get("keyword", "priority search demand") if opportunities else "priority search demand"
    top_finding = _top_finding(audit_result.get("findings", []), "High") or _top_finding(
        audit_result.get("findings", [])
    )
    top_recommendation = str(
        top_finding.get("recommendation", "tightening high-impact technical and content gaps")
    ).rstrip(".")

    sentence_one = (
        f"{company_name} currently shows {overall_health} SEO health across the sampled crawl, and the board-level reading is that {management_summary.get('board_verdict', 'SEO performance is mixed.').lower()}"
    )
    sentence_two = (
        f"The fastest near-term return should come from {top_recommendation.lower()}, while expanding coverage around {top_opportunity} can reduce the remaining {content_gap_ratio} competitor gap."
    )

    return f"{sentence_one} {sentence_two}"


def build_recommended_roadmap(
    audit_result: dict,
    comparison_result: dict,
) -> list[dict]:
    findings = audit_result.get("findings", [])
    high_findings = [finding for finding in findings if finding.get("priority") == "High"]
    medium_findings = [finding for finding in findings if finding.get("priority") == "Medium"]
    market_opportunities = comparison_result.get("market_opportunities", [])
    top_opportunity = market_opportunities[0] if market_opportunities else {}

    first_actions = [finding.get("recommendation", "") for finding in high_findings[:2]]
    if not first_actions:
        first_actions = [finding.get("recommendation", "") for finding in findings[:2]]

    second_actions = [finding.get("recommendation", "") for finding in medium_findings[:2]]
    if not second_actions:
        second_actions = [finding.get("recommendation", "") for finding in findings[2:4]]

    third_actions = [
        (
            f"Build or expand content targeting {top_opportunity.get('keyword', 'the top missing market opportunity')}."
        ),
        "Connect Search Console and analytics to tie SEO improvements to actual business outcomes.",
        "Run a full crawl and performance audit before the next management review cycle.",
    ]

    return [
        {
            "timeline": "0-30 days",
            "priority": "High",
            "objective": "Remove the highest-impact technical blockers from the sampled templates.",
            "actions": [action for action in first_actions if action],
            "expected_outcome": (
                "Cleaner crawling, stronger snippet quality, and a faster lift in baseline organic discoverability."
            ),
        },
        {
            "timeline": "31-60 days",
            "priority": "Medium",
            "objective": "Standardize metadata, page depth, and SERP enhancement coverage across key page types.",
            "actions": [action for action in second_actions if action],
            "expected_outcome": (
                "More consistent ranking signals across templates and better conversion readiness from organic traffic."
            ),
        },
        {
            "timeline": "61-90 days",
            "priority": "Medium",
            "objective": "Scale topical authority and measurement maturity.",
            "actions": third_actions,
            "expected_outcome": (
                "Clearer attribution of SEO impact and stronger competitive coverage on commercially important topics."
            ),
        },
    ]


def build_detailed_appendix(
    crawl_data: dict,
    primary_page_audit: dict,
    sitewide_audit: dict,
) -> dict:
    robots_status = crawl_data.get("robots", {}).get("status_code", 0)
    sitemap_status = crawl_data.get("sitemap", {}).get("status_code", 0)
    broken_summary = crawl_data.get("broken_link_summary", {})
    declared_sitemaps = crawl_data.get("declared_sitemaps", [])

    evidence_notes = [
        f"Robots.txt check returned status {robots_status}.",
        f"Sitemap endpoint check returned status {sitemap_status}.",
        (
            f"Broken-link sample found {broken_summary.get('broken_count', 0)} broken internal links "
            f"across {broken_summary.get('checked_count', 0)} checked URLs."
        ),
        (
            f"Declared sitemap references found in robots.txt: {len(declared_sitemaps)}."
        ),
        (
            f"Sample crawl analyzed {crawl_data.get('analyzed_pages', 0)} pages out of "
            f"{crawl_data.get('discovered_internal_pages', 0)} discovered internal URLs."
        ),
    ]

    return {
        "primary_page_url": crawl_data.get("primary_page", {}).get("url", ""),
        "primary_page_audit": primary_page_audit,
        "page_summaries": sitewide_audit.get("page_summaries", []),
        "evidence_notes": evidence_notes,
    }


def build_pdf_template_data(
    url: str,
    executive_summary: str,
    management_summary: dict,
    audit_result: dict,
    comparison_result: dict,
    crawl_data: dict,
    site_profile: dict,
    data_limitations: list[dict],
) -> dict:
    company_name = _safe_company_name(site_profile)
    audience_label = site_profile.get("audience_label") or DEFAULT_REPORT_AUDIENCE
    business_summary = site_profile.get("business_summary") or company_name
    category_scores = audit_result.get("category_scores", {})
    findings = audit_result.get("findings", [])
    market_opportunities = comparison_result.get("market_opportunities", [])

    priority_actions = [
        {
            "priority": finding["priority"],
            "headline": finding["metric"],
            "action": finding["recommendation"],
            "business_impact": finding["business_impact"],
        }
        for finding in findings[:4]
    ]

    crawl_overview = [
        {
            "label": "Pages Sampled",
            "value": str(crawl_data.get("analyzed_pages", 0)),
        },
        {
            "label": "Internal URLs Discovered",
            "value": str(crawl_data.get("discovered_internal_pages", 0)),
        },
        {
            "label": "Sample Coverage",
            "value": f"{crawl_data.get('sample_coverage_ratio', 0.0)}%",
        },
        {
            "label": "Favicon Status",
            "value": "Found" if (crawl_data.get("favicon", {}).get("exists") or crawl_data.get("primary_page", {}).get("has_favicon")) else "Missing",
        },
        {
            "label": "Broken Link Ratio",
            "value": f"{crawl_data.get('broken_link_summary', {}).get('broken_ratio', 0.0)}%",
        },
    ]

    return {
        "report_title": "Management SEO Audit Report",
        "prepared_for": f"{company_name} {audience_label}",
        "website": url,
        "generated_on": date.today().isoformat(),
        "executive_summary": executive_summary,
        "board_verdict": management_summary.get("board_verdict", ""),
        "hero_metrics": [
            {
                "label": "Overall SEO Health",
                "value": audit_result.get("overall_seo_health", "0%"),
            },
            {
                "label": "Metadata Health",
                "value": category_scores.get("metadata", "0%"),
            },
            {
                "label": "Content Depth",
                "value": category_scores.get("content_depth", "0%"),
            },
            {
                "label": "Competitor Gap",
                "value": comparison_result.get("content_gap_ratio", "0%"),
            },
        ],
        "crawl_overview": crawl_overview,
        "priority_actions": priority_actions,
        "market_opportunities": market_opportunities[:3],
        "data_limitations": data_limitations,
        "company_name": company_name,
        "business_summary": business_summary,
    }
