import asyncio
import json
import re
from collections import deque
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import (
    BROKEN_LINK_CHECK_LIMIT,
    CRAWL_MAX_DEPTH,
    CRAWL_MAX_PAGES,
)

CRAWL_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def normalize_crawl_url(url: str) -> str:
    normalized_url, _fragment = urldefrag(url.strip())
    parsed = urlparse(normalized_url)
    normalized_netloc = parsed.netloc.lower()
    normalized_path = parsed.path or "/"

    if normalized_path != "/" and normalized_path.endswith("/"):
        normalized_path = normalized_path.rstrip("/")

    return parsed._replace(netloc=normalized_netloc, path=normalized_path).geturl()


def _same_domain(base_domain: str, candidate_url: str) -> bool:
    candidate_domain = urlparse(candidate_url).netloc.lower()
    base_domain = base_domain.lower()

    return (
        candidate_domain == base_domain
        or candidate_domain.endswith(f".{base_domain}")
        or base_domain.endswith(f".{candidate_domain}")
    )


def _extract_meta_content(soup: BeautifulSoup, attr_name: str, attr_value: str) -> str:
    meta_tag = soup.find(
        "meta",
        attrs={attr_name: lambda value: value and value.lower() == attr_value.lower()},
    )
    if meta_tag and meta_tag.get("content"):
        return meta_tag.get("content").strip()
    return ""


def _extract_text_word_count(soup: BeautifulSoup) -> int:
    body = soup.body or soup
    clean_soup = BeautifulSoup(str(body), "lxml")

    for tag in clean_soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    text = clean_soup.get_text(" ", strip=True)
    words = re.findall(r"\b[\w'-]+\b", text)
    return len(words)


def _extract_structured_data_types(soup: BeautifulSoup) -> list[str]:
    types = []

    for script in soup.find_all("script", attrs={"type": lambda value: value and "ld+json" in value.lower()}):
        raw_text = script.string or script.get_text(strip=True)
        if not raw_text:
            continue

        try:
            parsed = json.loads(raw_text)
        except Exception:
            continue

        stack = parsed if isinstance(parsed, list) else [parsed]

        while stack:
            item = stack.pop()

            if isinstance(item, dict):
                item_type = item.get("@type")
                if isinstance(item_type, str):
                    types.append(item_type)
                elif isinstance(item_type, list):
                    types.extend(value for value in item_type if isinstance(value, str))

                graph_items = item.get("@graph")
                if isinstance(graph_items, list):
                    stack.extend(graph_items)

            elif isinstance(item, list):
                stack.extend(item)

    if soup.find(attrs={"itemscope": True}):
        types.append("Microdata")

    deduped_types = []
    seen = set()
    for item_type in types:
        cleaned_type = str(item_type).strip()
        if not cleaned_type:
            continue
        if cleaned_type.lower() in seen:
            continue
        seen.add(cleaned_type.lower())
        deduped_types.append(cleaned_type)

    return deduped_types


def _classify_page_type(url: str) -> str:
    path = urlparse(url).path.lower().strip("/")

    if not path:
        return "Homepage"
    if any(part in path for part in ["contact", "get-in-touch", "book", "demo"]):
        return "Contact/Conversion"
    if any(part in path for part in ["about", "company", "team"]):
        return "About/Trust"
    if any(part in path for part in ["blog", "news", "article", "post", "insight"]):
        return "Blog/Resource"
    if any(part in path for part in ["service", "solution", "product", "platform"]):
        return "Service/Product"
    return "Other"


def _parse_page(response: httpx.Response, depth: int, base_domain: str) -> dict:
    soup = BeautifulSoup(response.text, "lxml")
    final_url = normalize_crawl_url(str(response.url))

    title = soup.title.get_text(strip=True) if soup.title else ""
    description = _extract_meta_content(soup, "name", "description")
    viewport_content = _extract_meta_content(soup, "name", "viewport")
    robots_directives = _extract_meta_content(soup, "name", "robots").lower()

    headings = {}
    for index in range(1, 7):
        tag_name = f"h{index}"
        headings[tag_name] = [
            heading.get_text(" ", strip=True)
            for heading in soup.find_all(tag_name)
        ]

    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value.lower())
    canonical_href = ""
    if canonical_tag and canonical_tag.get("href"):
        canonical_href = normalize_crawl_url(urljoin(final_url, canonical_tag["href"]))

    images = soup.find_all("img")
    missing_alt_images = [
        image.get("src") or "inline-image"
        for image in images
        if not (image.get("alt") or "").strip()
    ]

    internal_links = []
    external_links = []
    seen_links = set()

    for anchor in soup.find_all("a", href=True):
        href = urljoin(final_url, anchor["href"])
        normalized_href = normalize_crawl_url(href)
        parsed_href = urlparse(normalized_href)

        if parsed_href.scheme not in {"http", "https"}:
            continue

        if normalized_href in seen_links:
            continue

        seen_links.add(normalized_href)

        if _same_domain(base_domain, normalized_href):
            internal_links.append(normalized_href)
        else:
            external_links.append(normalized_href)

    open_graph_tags = soup.find_all(
        "meta",
        attrs={"property": lambda value: value and value.lower().startswith("og:")},
    )
    twitter_tags = soup.find_all(
        "meta",
        attrs={"name": lambda value: value and value.lower().startswith("twitter:")},
    )
    structured_data_types = _extract_structured_data_types(soup)

    return {
        "url": final_url,
        "depth": depth,
        "status_code": response.status_code,
        "title": title,
        "title_length": len(title),
        "description": description,
        "meta_description_length": len(description),
        "canonical_url": canonical_href,
        "has_canonical": bool(canonical_href),
        "has_viewport_meta": bool(viewport_content),
        "robots_directives": robots_directives,
        "is_indexable": "noindex" not in robots_directives,
        "headings": headings,
        "h1_count": len(headings["h1"]),
        "word_count": _extract_text_word_count(soup),
        "total_images": len(images),
        "missing_alt_images": missing_alt_images,
        "internal_links_count": len(internal_links),
        "external_links_count": len(external_links),
        "internal_links": internal_links,
        "external_links": external_links,
        "has_open_graph": bool(open_graph_tags),
        "has_twitter_card": bool(twitter_tags),
        "has_structured_data": bool(structured_data_types),
        "structured_data_types": structured_data_types,
        "page_type": _classify_page_type(final_url),
    }


async def _fetch_supporting_resource(client: httpx.AsyncClient, target_url: str) -> dict:
    try:
        response = await client.get(target_url, headers=CRAWL_HEADERS, follow_redirects=True)
        return {
            "url": str(response.url),
            "status_code": response.status_code,
            "exists": response.status_code == 200,
            "body": response.text if response.status_code == 200 else "",
        }
    except Exception as exc:
        return {
            "url": target_url,
            "status_code": 0,
            "exists": False,
            "body": "",
            "error": str(exc),
        }


async def _check_link_status(
    client: httpx.AsyncClient,
    target_url: str,
    source_url: str,
) -> dict:
    try:
        response = await client.get(target_url, headers=CRAWL_HEADERS, follow_redirects=True)
        status_code = response.status_code
    except Exception:
        status_code = 0

    return {
        "source_url": source_url,
        "target_url": target_url,
        "status_code": status_code,
        "is_broken": status_code == 0 or status_code >= 400,
    }


async def _check_sampled_internal_links(
    client: httpx.AsyncClient,
    pages: list[dict],
) -> dict:
    checked_links = []
    seen_targets = set()

    for page in pages:
        for target_url in page["internal_links"]:
            if target_url in seen_targets:
                continue

            seen_targets.add(target_url)

            if len(checked_links) >= BROKEN_LINK_CHECK_LIMIT:
                break

            checked_links.append((target_url, page["url"]))

        if len(checked_links) >= BROKEN_LINK_CHECK_LIMIT:
            break

    if not checked_links:
        return {
            "checked_count": 0,
            "broken_count": 0,
            "broken_ratio": 0.0,
            "broken_links": [],
        }

    results = await asyncio.gather(
        *(
            _check_link_status(client, target_url=target_url, source_url=source_url)
            for target_url, source_url in checked_links
        )
    )

    broken_links = [item for item in results if item["is_broken"]]
    broken_ratio = (len(broken_links) / len(results)) * 100 if results else 0.0

    return {
        "checked_count": len(results),
        "broken_count": len(broken_links),
        "broken_ratio": round(broken_ratio, 1),
        "broken_links": broken_links[:5],
    }


async def crawl_site(start_url: str) -> dict:
    normalized_start_url = normalize_crawl_url(start_url)
    base_domain = urlparse(normalized_start_url).netloc

    async with httpx.AsyncClient(timeout=20.0) as client:
        robots_task = asyncio.create_task(
            _fetch_supporting_resource(client, urljoin(normalized_start_url, "/robots.txt"))
        )
        sitemap_task = asyncio.create_task(
            _fetch_supporting_resource(client, urljoin(normalized_start_url, "/sitemap.xml"))
        )

        queue = deque([(normalized_start_url, 0)])
        queued_urls = {normalized_start_url}
        visited_urls = set()
        discovered_urls = {normalized_start_url}
        pages = []
        page_map = {}
        max_depth_reached = 0

        while queue and len(pages) < CRAWL_MAX_PAGES:
            current_url, depth = queue.popleft()
            queued_urls.discard(current_url)

            if current_url in visited_urls:
                continue

            visited_urls.add(current_url)

            try:
                response = await client.get(
                    current_url,
                    headers=CRAWL_HEADERS,
                    follow_redirects=True,
                )
                response.raise_for_status()
            except Exception:
                continue

            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                continue

            page_data = _parse_page(response, depth=depth, base_domain=base_domain)
            final_url = page_data["url"]

            if final_url in page_map:
                continue

            page_map[final_url] = page_data
            pages.append(page_data)
            max_depth_reached = max(max_depth_reached, depth)

            for link in page_data["internal_links"]:
                discovered_urls.add(link)

                if (
                    depth < CRAWL_MAX_DEPTH
                    and link not in visited_urls
                    and link not in queued_urls
                    and len(visited_urls) < CRAWL_MAX_PAGES
                ):
                    queue.append((link, depth + 1))
                    queued_urls.add(link)

        robots_data, sitemap_data = await asyncio.gather(robots_task, sitemap_task)
        broken_link_summary = await _check_sampled_internal_links(client, pages)

    declared_sitemaps = []
    for line in robots_data.get("body", "").splitlines():
        if line.lower().startswith("sitemap:"):
            sitemap_url = line.split(":", 1)[1].strip()
            if sitemap_url:
                declared_sitemaps.append(sitemap_url)

    primary_page = pages[0] if pages else {}
    sample_coverage_ratio = (
        round((len(pages) / len(discovered_urls)) * 100, 1)
        if discovered_urls
        else 0.0
    )

    return {
        "base_url": normalized_start_url,
        "domain": base_domain,
        "pages": pages,
        "primary_page": primary_page,
        "analyzed_pages": len(pages),
        "discovered_internal_pages": len(discovered_urls),
        "sample_coverage_ratio": sample_coverage_ratio,
        "crawl_depth": max_depth_reached,
        "robots": robots_data,
        "sitemap": sitemap_data,
        "declared_sitemaps": declared_sitemaps,
        "broken_link_summary": broken_link_summary,
    }
