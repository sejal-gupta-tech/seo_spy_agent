"""
Sitemap.xml Builder Service
──────────────────────────
Full sitemap discovery, parsing, crawling, XML generation,
metrics calculation, orphan detection, internal link scoring,
and warning engine for the SEO Spy Agent.
"""

import asyncio
import re
from collections import deque
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, urldefrag
from xml.etree import ElementTree as ET

import httpx
from bs4 import BeautifulSoup

from app.core.config import CRAWL_MAX_PAGES, HTTP_TIMEOUT_SECONDS
from app.core.logger import logger
from app.services.crawler import CRAWL_HEADERS, normalize_crawl_url, _same_domain


# ─── Constants ────────────────────────────────────────────────────────────────

_SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
_SKIP_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".pdf", ".zip", ".gz", ".tar", ".rar",
    ".css", ".js", ".woff", ".woff2", ".ttf", ".eot",
    ".mp3", ".mp4", ".avi", ".mov", ".wmv",
}
_SKIP_SCHEMES = {"mailto", "tel", "javascript", "data", "ftp"}


# ─── Step 1: Discover Sitemap ────────────────────────────────────────────────

async def discover_sitemap(
    client: httpx.AsyncClient,
    base_url: str,
) -> dict:
    """
    Check common sitemap locations and robots.txt for Sitemap directives.
    Returns {sitemap_found, sitemap_url, source}.
    """
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    # 1. Check /sitemap.xml
    for path, source_label in [
        ("/sitemap.xml", "sitemap.xml"),
        ("/sitemap_index.xml", "sitemap_index.xml"),
    ]:
        url = f"{origin}{path}"
        try:
            resp = await client.get(url, follow_redirects=True)
            ct = resp.headers.get("content-type", "").lower()
            body = resp.text
            if (
                resp.status_code == 200
                and "xml" in ct
                and ("<urlset" in body.lower() or "<sitemapindex" in body.lower())
            ):
                logger.info("[sitemap_builder] Found sitemap at %s", url)
                return {
                    "sitemap_found": True,
                    "sitemap_url": str(resp.url),
                    "source": source_label,
                }
        except Exception as exc:
            logger.debug("[sitemap_builder] Failed to fetch %s: %s", url, exc)

    # 2. Check robots.txt for Sitemap: directives
    robots_url = f"{origin}/robots.txt"
    try:
        resp = await client.get(robots_url, follow_redirects=True)
        if resp.status_code == 200 and "text/plain" in resp.headers.get("content-type", "").lower():
            for line in resp.text.splitlines():
                stripped = line.strip()
                if stripped.lower().startswith("sitemap:"):
                    sitemap_url = stripped.split(":", 1)[1].strip()
                    if sitemap_url.startswith("http"):
                        logger.info("[sitemap_builder] Found sitemap in robots.txt: %s", sitemap_url)
                        return {
                            "sitemap_found": True,
                            "sitemap_url": sitemap_url,
                            "source": "robots.txt",
                        }
    except Exception as exc:
        logger.debug("[sitemap_builder] Failed to fetch robots.txt: %s", exc)

    return {"sitemap_found": False, "sitemap_url": "", "source": ""}


# ─── Step 2: Parse Existing Sitemap ──────────────────────────────────────────

async def parse_sitemap(
    client: httpx.AsyncClient,
    sitemap_url: str,
    _visited: set | None = None,
) -> dict:
    """
    Recursively parse sitemap XML (including sitemap index files).
    Returns {total_urls, urls[]}.
    """
    if _visited is None:
        _visited = set()

    if sitemap_url in _visited:
        return {"total_urls": 0, "urls": []}
    _visited.add(sitemap_url)

    all_urls: list[str] = []

    try:
        resp = await client.get(sitemap_url, follow_redirects=True)
        if resp.status_code != 200:
            return {"total_urls": 0, "urls": []}

        body = resp.text
        root = ET.fromstring(body)

        # Detect namespace
        ns = ""
        match = re.match(r"\{(.+?)\}", root.tag)
        if match:
            ns = match.group(1)
        ns_map = {"ns": ns} if ns else {}

        # Check if it's a sitemap index
        sitemaps = root.findall("ns:sitemap", ns_map) if ns else root.findall("sitemap")
        if sitemaps:
            # Recursively process sub-sitemaps
            tasks = []
            for sm in sitemaps:
                loc_el = sm.find("ns:loc", ns_map) if ns else sm.find("loc")
                if loc_el is not None and loc_el.text:
                    sub_url = loc_el.text.strip()
                    if sub_url not in _visited:
                        tasks.append(parse_sitemap(client, sub_url, _visited))

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, dict):
                        all_urls.extend(result.get("urls", []))
        else:
            # Regular sitemap — extract <url><loc> entries
            url_elements = root.findall("ns:url", ns_map) if ns else root.findall("url")
            for url_el in url_elements:
                loc_el = url_el.find("ns:loc", ns_map) if ns else url_el.find("loc")
                if loc_el is not None and loc_el.text:
                    all_urls.append(loc_el.text.strip())

    except ET.ParseError as exc:
        logger.warning("[sitemap_builder] XML parse error for %s: %s", sitemap_url, exc)
    except Exception as exc:
        logger.warning("[sitemap_builder] Failed to parse sitemap %s: %s", sitemap_url, exc)

    # Deduplicate
    seen = set()
    deduped: list[str] = []
    for u in all_urls:
        normalized = normalize_crawl_url(u)
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)

    return {"total_urls": len(deduped), "urls": deduped}


# ─── Step 3: Crawl Website When Sitemap Missing ─────────────────────────────

def _should_skip_url(url: str) -> bool:
    """Return True if the URL should be excluded from crawling."""
    parsed = urlparse(url)
    if parsed.scheme in _SKIP_SCHEMES:
        return True
    path_lower = parsed.path.lower()
    for ext in _SKIP_EXTENSIONS:
        if path_lower.endswith(ext):
            return True
    return False


async def _fetch_robots_disallows(
    client: httpx.AsyncClient,
    origin: str,
) -> set[str]:
    """Parse robots.txt and return set of disallowed path prefixes for *."""
    disallowed: set[str] = set()
    try:
        resp = await client.get(f"{origin}/robots.txt", follow_redirects=True)
        if resp.status_code != 200:
            return disallowed
        current_agent = None
        for line in resp.text.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("user-agent:"):
                current_agent = stripped.split(":", 1)[1].strip()
            elif stripped.lower().startswith("disallow:") and current_agent == "*":
                path = stripped.split(":", 1)[1].strip()
                if path:
                    disallowed.add(path)
    except Exception:
        pass
    return disallowed


def _is_disallowed(url: str, disallowed_paths: set[str]) -> bool:
    """Check if a URL path matches any robots.txt disallow rule."""
    parsed = urlparse(url)
    path = parsed.path or "/"
    for rule in disallowed_paths:
        if path.startswith(rule):
            return True
    return False


async def crawl_for_urls(
    client: httpx.AsyncClient,
    start_url: str,
    max_pages: int = 100,
) -> dict:
    """
    BFS crawl from the start URL, extracting internal links.
    Returns {discovered_urls[], link_graph: {url: [incoming_urls]}}.
    """
    normalized_start = normalize_crawl_url(start_url)
    base_domain = urlparse(normalized_start).netloc
    origin = f"{urlparse(normalized_start).scheme}://{base_domain}"

    disallowed = await _fetch_robots_disallows(client, origin)

    queue: deque[str] = deque([normalized_start])
    visited: set[str] = set()
    discovered: set[str] = {normalized_start}
    # link_graph maps target_url → set of source_urls that link to it
    link_graph: dict[str, set[str]] = {}

    while queue and len(visited) < max_pages:
        current_url = queue.popleft()

        if current_url in visited:
            continue
        if _is_disallowed(current_url, disallowed):
            continue

        visited.add(current_url)
        logger.debug("[sitemap_builder] Crawling: %s (%d/%d)", current_url, len(visited), max_pages)

        try:
            resp = await client.get(current_url, follow_redirects=True)
            if resp.status_code != 200:
                continue
            ct = resp.headers.get("content-type", "").lower()
            if "text/html" not in ct:
                continue

            soup = BeautifulSoup(resp.text, "lxml")

            for anchor in soup.find_all("a", href=True):
                raw_href = anchor["href"].strip()
                if not raw_href:
                    continue

                # Skip non-HTTP schemes
                if any(raw_href.lower().startswith(s + ":") for s in _SKIP_SCHEMES):
                    continue

                absolute = urljoin(current_url, raw_href)
                absolute, _ = urldefrag(absolute)
                normalized = normalize_crawl_url(absolute)

                if _should_skip_url(normalized):
                    continue
                if not _same_domain(base_domain, normalized):
                    continue

                # Track link graph
                if normalized not in link_graph:
                    link_graph[normalized] = set()
                link_graph[normalized].add(current_url)

                if normalized not in discovered:
                    discovered.add(normalized)
                    queue.append(normalized)

        except Exception as exc:
            logger.debug("[sitemap_builder] Crawl error for %s: %s", current_url, exc)

    discovered_list = sorted(discovered)
    # Serialize link_graph sets to lists
    serialized_graph = {url: list(sources) for url, sources in link_graph.items()}

    return {
        "discovered_urls": discovered_list,
        "link_graph": serialized_graph,
    }


# ─── Step 4: Generate Sitemap XML ────────────────────────────────────────────

def _get_priority(url: str) -> str:
    path = urlparse(url).path.lower().rstrip("/")
    if not path or path == "/":
        return "1.00"
    if re.match(r"^/(services?|products?|solutions?|work|portfolio)", path):
        return "0.90"
    if re.match(r"^/(category|categories|collection|directory|shop|store)", path):
        return "0.80"
    if re.match(r"^/(blog|news|articles?|insights?|posts?|updates?)", path):
        return "0.70"
    if re.match(r"^/(about|contact|team|faq|support|company)", path):
        return "0.64"
    if re.match(r"^/(privacy|terms|legal|cookies|disclaimer|gdpr)", path):
        return "0.30"
    return "0.50"


def _get_changefreq(url: str) -> str:
    path = urlparse(url).path.lower().rstrip("/")
    if not path or path == "/":
        return "daily"
    if re.match(r"^/(blog|news|articles?|insights?|posts?|updates?)", path):
        return "weekly"
    if re.match(r"^/(products?|items?|services?)", path):
        return "weekly"
    if re.match(r"^/(about|contact|team|faq|support|company)", path):
        return "monthly"
    return "monthly"


def generate_sitemap_xml(urls: list[str]) -> str:
    """
    Generate a valid XML sitemap string from a list of URLs.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9'
        ' http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">',
    ]

    for url in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{url}</loc>")
        lines.append(f"    <lastmod>{now}</lastmod>")
        lines.append(f"    <changefreq>{_get_changefreq(url)}</changefreq>")
        lines.append(f"    <priority>{_get_priority(url)}</priority>")
        lines.append("  </url>")

    lines.append("</urlset>")
    return "\n".join(lines)


# ─── Step 5: Calculate Sitemap Metrics ────────────────────────────────────────

def calculate_metrics(
    sitemap_urls: list[str],
    crawled_urls: list[str],
    orphan_pages: list[str],
    broken_urls: list[dict],
) -> dict:
    """Compute coverage and health metrics."""
    all_set = set(sitemap_urls) | set(crawled_urls)
    total = len(all_set)
    included = len(sitemap_urls) if sitemap_urls else total
    crawlable = total - len(broken_urls)
    coverage = round((included / total) * 100, 1) if total > 0 else 0

    return {
        "total_urls": total,
        "included": included,
        "crawlable": max(0, crawlable),
        "orphans": len(orphan_pages),
        "duplicates": 0,
        "broken": len(broken_urls),
        "coverage": coverage,
    }


# ─── Step 6: Detect Orphan Pages ─────────────────────────────────────────────

def detect_orphan_pages(
    all_urls: list[str],
    link_graph: dict[str, list[str]],
) -> list[str]:
    """
    Identify pages with zero incoming internal links.
    The link_graph maps target_url → [source_urls].
    """
    orphans = []
    for url in all_urls:
        incoming = link_graph.get(url, [])
        if len(incoming) == 0:
            orphans.append(url)
    return orphans


# ─── Step 7: Internal Link Score ─────────────────────────────────────────────

def calculate_internal_link_score(
    all_urls: list[str],
    link_graph: dict[str, list[str]],
) -> dict:
    """
    Calculate internal link score and rating.
    """
    total_pages = len(all_urls)
    if total_pages == 0:
        return {
            "score": 0,
            "rating": "Poor",
            "avg_links_per_page": 0,
            "issues": ["No pages discovered."],
            "recommendations": ["Add content and internal links to your website."],
        }

    # Count total incoming links across all pages
    total_incoming_links = sum(len(sources) for sources in link_graph.values())
    avg_links = round(total_incoming_links / total_pages, 1) if total_pages > 0 else 0

    # Count orphan pages
    orphan_count = sum(1 for url in all_urls if len(link_graph.get(url, [])) == 0)

    score = 100
    issues = []
    recommendations = []

    # Score deductions based on average links
    if avg_links < 1:
        score = 20
        issues.append(f"Very low average internal links per page ({avg_links}).")
        recommendations.append("Each page should link to at least 3-5 related pages.")
    elif avg_links < 3:
        score = 45
        issues.append(f"Low average internal links per page ({avg_links}).")
        recommendations.append("Increase internal linking to distribute authority across pages.")
    elif avg_links < 8:
        score = 70
        issues.append(f"Moderate internal linking density ({avg_links} links/page).")
        recommendations.append("Add more contextual internal links to key commercial pages.")

    # Orphan penalty
    if orphan_count > 0:
        orphan_penalty = min(25, orphan_count * 4)
        score = max(0, score - orphan_penalty)
        issues.append(f"{orphan_count} page(s) have zero incoming internal links (orphans).")
        recommendations.append("Add internal links pointing to orphan pages from related content.")

    # Determine rating
    if score >= 80:
        rating = "Excellent"
    elif score >= 60:
        rating = "Good"
    elif score >= 40:
        rating = "Average"
    else:
        rating = "Poor"

    return {
        "score": score,
        "rating": rating,
        "avg_links_per_page": avg_links,
        "issues": issues,
        "recommendations": recommendations,
    }


# ─── Step 8: Generate Warnings ───────────────────────────────────────────────

def generate_warnings(
    sitemap_discovery: dict,
    metrics: dict,
    orphan_pages: list[str],
    broken_urls: list[dict],
    internal_link_score: dict,
) -> list[dict]:
    """
    Produce severity-tagged warnings.
    Returns list of {severity, message, rule}.
    """
    warnings: list[dict] = []

    # Rule 1: Missing sitemap
    if not sitemap_discovery.get("sitemap_found"):
        warnings.append({
            "severity": "Critical",
            "message": "No sitemap.xml detected on the server. Search engines cannot efficiently discover your pages.",
            "rule": "missing_sitemap",
        })

    # Rule 2: Low coverage
    coverage = metrics.get("coverage", 0)
    if coverage < 50:
        warnings.append({
            "severity": "Critical",
            "message": f"Sitemap coverage is critically low ({coverage}%). Many pages may not be indexed.",
            "rule": "low_coverage",
        })
    elif coverage < 80:
        warnings.append({
            "severity": "Warning",
            "message": f"Sitemap coverage is below optimal ({coverage}%). Consider adding missing pages.",
            "rule": "low_coverage",
        })

    # Rule 3: Orphan pages
    if len(orphan_pages) > 0:
        warnings.append({
            "severity": "Warning",
            "message": f"{len(orphan_pages)} orphan page(s) detected with no incoming internal links.",
            "rule": "orphan_pages",
        })

    # Rule 4: Broken URLs
    if len(broken_urls) > 0:
        warnings.append({
            "severity": "Critical",
            "message": f"{len(broken_urls)} broken URL(s) found that return error status codes.",
            "rule": "broken_urls",
        })

    # Rule 5: Low internal link score
    link_score = internal_link_score.get("score", 100)
    if link_score < 40:
        warnings.append({
            "severity": "Warning",
            "message": f"Internal link score is poor ({link_score}/100). Weak internal linking hurts crawlability.",
            "rule": "low_link_score",
        })

    # Rule 6: Informational — sitemap found
    if sitemap_discovery.get("sitemap_found"):
        source = sitemap_discovery.get("source", "unknown")
        warnings.append({
            "severity": "Info",
            "message": f"Existing sitemap detected via {source}. URLs have been merged with crawl data.",
            "rule": "sitemap_detected",
        })

    # Rule 7: AI crawler access
    warnings.append({
        "severity": "Info",
        "message": "Ensure robots.txt allows GPTBot, ClaudeBot, and PerplexityBot for AI search indexing.",
        "rule": "ai_crawler_access",
    })

    return warnings


# ─── Step 9: Check Broken URLs (sampled) ─────────────────────────────────────

async def check_broken_urls(
    client: httpx.AsyncClient,
    urls: list[str],
    limit: int = 30,
) -> list[dict]:
    """
    HEAD-check a sample of URLs for broken (4xx/5xx) status codes.
    """
    sample = urls[:limit]
    broken: list[dict] = []

    async def _check(url: str) -> dict | None:
        try:
            resp = await client.head(url, follow_redirects=True)
            if resp.status_code >= 400:
                return {"url": url, "status_code": resp.status_code}
        except Exception:
            return {"url": url, "status_code": 0}
        return None

    results = await asyncio.gather(*(_check(u) for u in sample), return_exceptions=True)
    for r in results:
        if isinstance(r, dict):
            broken.append(r)

    return broken


# ─── Master Orchestrator ─────────────────────────────────────────────────────

async def run_sitemap_analysis(
    url: str,
    max_pages: int = 100,
) -> dict:
    """
    Master function that chains all steps and returns a comprehensive
    sitemap analysis payload.
    """
    logger.info("[sitemap_builder] Starting sitemap analysis for: %s", url)

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(HTTP_TIMEOUT_SECONDS, connect=min(5.0, HTTP_TIMEOUT_SECONDS)),
        headers=CRAWL_HEADERS,
    ) as client:

        # Step 1: Discover existing sitemap
        discovery = await discover_sitemap(client, url)
        logger.info("[sitemap_builder] Discovery result: %s", discovery)

        # Step 2: Parse existing sitemap if found
        sitemap_urls: list[str] = []
        if discovery["sitemap_found"]:
            parsed = await parse_sitemap(client, discovery["sitemap_url"])
            sitemap_urls = parsed.get("urls", [])
            logger.info("[sitemap_builder] Parsed %d URLs from existing sitemap", len(sitemap_urls))

        # Step 3: Crawl the website
        crawl_result = await crawl_for_urls(client, url, max_pages=max_pages)
        crawled_urls = crawl_result.get("discovered_urls", [])
        link_graph = crawl_result.get("link_graph", {})
        logger.info("[sitemap_builder] Crawled %d URLs", len(crawled_urls))

        # Merge & deduplicate
        merged_set = set(sitemap_urls) | set(crawled_urls)
        all_urls = sorted(merged_set)

        # Step 9: Check broken URLs (before metrics)
        broken_urls = await check_broken_urls(client, all_urls)
        logger.info("[sitemap_builder] Found %d broken URLs", len(broken_urls))

    # Step 4: Generate sitemap XML
    xml_content = generate_sitemap_xml(all_urls)

    # Step 6: Detect orphans
    orphan_pages = detect_orphan_pages(all_urls, link_graph)

    # Step 5: Calculate metrics
    metrics = calculate_metrics(sitemap_urls, crawled_urls, orphan_pages, broken_urls)

    # Step 7: Internal link score
    internal_score = calculate_internal_link_score(all_urls, link_graph)

    # Step 8: Generate warnings
    warnings = generate_warnings(discovery, metrics, orphan_pages, broken_urls, internal_score)

    logger.info(
        "[sitemap_builder] Analysis complete for %s — %d URLs, %d orphans, %d warnings",
        url, len(all_urls), len(orphan_pages), len(warnings),
    )

    return {
        "url": url,
        "sitemap_discovery": discovery,
        "sitemap_urls": sitemap_urls,
        "crawled_urls": crawled_urls,
        "all_urls": all_urls,
        "sitemap_xml": xml_content,
        "metrics": metrics,
        "orphan_pages": orphan_pages,
        "internal_link_score": internal_score,
        "warnings": warnings,
        "broken_urls": broken_urls,
    }
