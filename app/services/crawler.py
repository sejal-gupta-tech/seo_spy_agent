import asyncio
import json
import re
from collections import deque
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import (
    BROKEN_LINK_CHECK_LIMIT,
    CRAWL_RETRY_DELAY_SECONDS,
    CRAWL_MAX_DEPTH,
    CRAWL_MAX_PAGES,
    HTTP_TIMEOUT_SECONDS,
)
from app.services.progress import ProgressCallback, emit_progress

CRAWL_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}


def _describe_crawl_failure(
    status_code: int | None = None,
    error: Exception | None = None,
) -> tuple[str, str]:
    if status_code == 401:
        return "blocked", "Authentication is required before this page can be crawled (401)."
    if status_code == 403:
        return "blocked", "This page is blocked by access controls or bot protection (403)."
    if status_code == 404:
        return "missing", "This page returns 404 and is no longer available."
    if status_code == 405:
        return "blocked", "The origin refused this crawl method (405)."
    if status_code == 429:
        return "rate_limited", "The site is rate-limiting crawl requests (429)."
    if status_code and 500 <= status_code < 600:
        return "server", f"The site returned a server error ({status_code})."
    if status_code and 400 <= status_code < 500:
        return "client", f"The page returned an unexpected client error ({status_code})."

    if isinstance(error, (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.WriteTimeout)):
        return "timeout", "The page timed out before it could be read."
    if isinstance(error, httpx.TooManyRedirects):
        return "redirect_loop", "The page entered a redirect loop and could not be resolved."
    if isinstance(error, httpx.ConnectError):
        return "network", "The crawler could not establish a network connection."

    return "network", "The request failed before the page could be analyzed."


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

    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in str(value).lower())
    canonical_href = ""
    if canonical_tag and canonical_tag.get("href"):
        canonical_href = normalize_crawl_url(urljoin(final_url, canonical_tag["href"]))

    # Only standard favicon link tags count as a favicon.
    # apple-touch-icon, mask-icon, etc. are NOT favicons and must be excluded.
    _FAVICON_REL_VALUES = {"icon", "shortcut icon"}

    def _is_favicon_rel(value) -> bool:
        if not value:
            return False
        # rel attribute can be a list (BeautifulSoup) or a string
        rels = value if isinstance(value, list) else str(value).split()
        return any(r.lower().strip() in _FAVICON_REL_VALUES for r in rels)

    favicon_tag = soup.find("link", rel=_is_favicon_rel)
    favicon_href = ""
    if favicon_tag and favicon_tag.get("href"):
        raw_href = favicon_tag["href"].strip()
        if raw_href and not raw_href.startswith("data:"):
            favicon_href = normalize_crawl_url(urljoin(final_url, raw_href))

    images = soup.find_all("img")
    missing_alt_images = [
        image.get("src") or "inline-image"
        for image in images
        if not (image.get("alt") or "").strip()
    ]

    internal_links = []
    internal_link_anchors = []
    internal_link_targets = []
    external_links = []
    external_domains_set = set()
    dofollow_links = 0
    nofollow_links = 0
    seen_links = set()

    for anchor in soup.find_all("a", href=True):
        href = urljoin(final_url, anchor["href"])
        normalized_href = normalize_crawl_url(href)
        parsed_href = urlparse(normalized_href)

        if parsed_href.scheme not in {"http", "https"}:
            continue

        rel_attr = anchor.get("rel", [])
        if "nofollow" in str(rel_attr).lower():
            nofollow_links += 1
        else:
            dofollow_links += 1

        if normalized_href in seen_links:
            continue

        seen_links.add(normalized_href)

        if _same_domain(base_domain, normalized_href):
            internal_links.append(normalized_href)
            internal_link_targets.append(normalized_href)
            anchor_text = anchor.get_text(separator=" ", strip=True)
            if anchor_text and anchor_text not in internal_link_anchors:
                internal_link_anchors.append(anchor_text)
        else:
            external_links.append(normalized_href)
            if parsed_href.netloc:
                external_domains_set.add(parsed_href.netloc)

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
        "favicon_url": favicon_href,
        "has_favicon": bool(favicon_href),
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
        "internal_link_anchors": internal_link_anchors,
        "internal_link_targets": internal_link_targets,
        "external_links": external_links,
        "external_domains": list(external_domains_set),
        "dofollow_links": dofollow_links,
        "nofollow_links": nofollow_links,
        "has_open_graph": bool(open_graph_tags),
        "has_twitter_card": bool(twitter_tags),
        "has_structured_data": bool(structured_data_types),
        "structured_data_types": structured_data_types,
        "page_type": _classify_page_type(final_url),
    }


async def _fetch_supporting_resource(client: httpx.AsyncClient, target_url: str) -> dict:
    """Generic HEAD/GET checker for robots.txt, sitemap.xml, etc."""
    try:
        response = await client.get(target_url, headers=CRAWL_HEADERS, follow_redirects=True)
        return {
            "url": str(response.url),
            "status_code": response.status_code,
            "exists": response.status_code == 200,
            "body": response.text if response.status_code == 200 else "",
            "status_string": f"Found ({response.status_code})" if response.status_code == 200 else "Missing"
        }
    except Exception as exc:
        return {
            "url": target_url,
            "status_code": 0,
            "exists": False,
            "body": "",
            "status_string": "Missing",
            "error": str(exc),
        }


async def _fetch_favicon(client: httpx.AsyncClient, target_url: str) -> dict:
    """
    Fetches /favicon.ico and validates it is actually an image.
    Many servers return HTTP 200 with an HTML error page at /favicon.ico when
    no favicon exists — content-type validation catches these false positives.
    """
    _IMAGE_TYPES = {
        "image/x-icon", "image/vnd.microsoft.icon", "image/png",
        "image/jpeg", "image/gif", "image/svg+xml", "image/webp",
    }
    try:
        response = await client.get(target_url, headers=CRAWL_HEADERS, follow_redirects=True)
        content_type = response.headers.get("content-type", "").lower().split(";")[0].strip()
        status_code = response.status_code

        # A 200 with an HTML body is NOT a valid favicon (CDN / server error page)
        is_image = any(ct in content_type for ct in ("image/",))
        is_html = "text/html" in content_type or (
            response.text.lstrip()[:15].lower().startswith(("<!doctype", "<html"))
        )

        exists = status_code == 200 and is_image and not is_html
        status_string = (
            f"Found ({status_code} · {content_type})" if exists
            else "Missing" if status_code != 200
            else f"Invalid (HTTP 200 but content-type is '{content_type}', not an image)"
        )

        return {
            "url": str(response.url),
            "status_code": status_code,
            "exists": exists,
            "content_type": content_type,
            "status_string": status_string,
            "body": "",
        }
    except Exception as exc:
        return {
            "url": target_url,
            "status_code": 0,
            "exists": False,
            "content_type": "",
            "status_string": "Missing",
            "body": "",
            "error": str(exc),
        }

async def _fetch_robots_txt(client: httpx.AsyncClient, target_url: str) -> dict:
    try:
        response = await client.get(target_url, headers=CRAWL_HEADERS, follow_redirects=True)
        content_type = response.headers.get("content-type", "").lower()
        body = response.text
        
        final_url_path = urlparse(str(response.url)).path
        if final_url_path == "" or final_url_path == "/":
            status = "Invalid (Redirected to homepage)"
            exists = False
        elif response.status_code != 200:
            status = "Missing"
            exists = False
        elif not body.strip():
            status = "Invalid (Empty response)"
            exists = False
        elif "text/html" in content_type or "<html" in body.lower():
            status = "Invalid (HTML response)"
            exists = False
        elif "text/plain" not in content_type:
            status = "Invalid (Wrong Content-Type)"
            exists = False
        elif not any(x in body.lower() for x in ["user-agent", "disallow", "allow"]):
            status = "Invalid (Missing directives)"
            exists = False
        else:
            status = "Found (Valid)"
            exists = True

        return {
            "url": str(response.url),
            "status_code": response.status_code,
            "exists": exists,
            "status_string": status,
            "body": body if exists else "",
        }
    except Exception as exc:
        return {
            "url": target_url, "status_code": 0, "exists": False,
            "status_string": "Missing", "body": "", "error": str(exc),
        }

async def _fetch_sitemap_xml(client: httpx.AsyncClient, target_url: str) -> dict:
    try:
        response = await client.get(target_url, headers=CRAWL_HEADERS, follow_redirects=True)
        content_type = response.headers.get("content-type", "").lower()
        body = response.text

        final_url_path = urlparse(str(response.url)).path
        if final_url_path == "" or final_url_path == "/":
            status = "Invalid (Redirected to homepage)"
            exists = False
        elif response.status_code != 200:
            status = "Missing"
            exists = False
        elif not body.strip():
            status = "Invalid (Empty response)"
            exists = False
        elif "text/html" in content_type or "<html" in body.lower():
            status = "Invalid (HTML response)"
            exists = False
        elif "xml" not in content_type:
            status = "Invalid (Wrong Content-Type)"
            exists = False
        elif "<urlset" not in body.lower() and "<sitemapindex" not in body.lower():
            status = "Invalid (Missing XML structure)"
            exists = False
        else:
            status = "Found (Valid)"
            exists = True

        return {
            "url": str(response.url),
            "status_code": response.status_code,
            "exists": exists,
            "status_string": status,
            "body": body if exists else "",
        }
    except Exception as exc:
        return {
            "url": target_url, "status_code": 0, "exists": False,
            "status_string": "Missing", "body": "", "error": str(exc),
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


async def crawl_site(
    start_url: str,
    max_pages: int | None = None,
    progress_callback: ProgressCallback | None = None,
) -> dict:
    normalized_start_url = normalize_crawl_url(start_url)
    base_domain = urlparse(normalized_start_url).netloc

    # 0 means "no limit" — crawl every discovered page
    _configured_max = max_pages if max_pages is not None else CRAWL_MAX_PAGES
    effective_max_pages = _configured_max if _configured_max > 0 else float("inf")
    display_max_pages = _configured_max if _configured_max > 0 else 9999  # for UI only

    await emit_progress(
        progress_callback,
        {
            "type": "crawl_seed",
            "url": normalized_start_url,
            "depth": 0,
            "max_pages": display_max_pages,
            "max_depth": CRAWL_MAX_DEPTH,
        },
    )

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(HTTP_TIMEOUT_SECONDS, connect=min(4.0, HTTP_TIMEOUT_SECONDS)),
        headers=CRAWL_HEADERS,
        follow_redirects=True,
    ) as client:
        robots_task = asyncio.create_task(
            _fetch_robots_txt(client, urljoin(normalized_start_url, "/robots.txt"))
        )
        sitemap_task = asyncio.create_task(
            _fetch_sitemap_xml(client, urljoin(normalized_start_url, "/sitemap.xml"))
        )
        favicon_task = asyncio.create_task(
            _fetch_favicon(client, urljoin(normalized_start_url, "/favicon.ico"))
        )

        queue = deque([(normalized_start_url, 0)])
        queued_urls = {normalized_start_url}
        visited_urls = set()
        discovered_urls = {normalized_start_url}
        pages = []
        page_map = {}
        max_depth_reached = 0

        while queue and len(pages) < effective_max_pages:
            current_url, depth = queue.popleft()
            queued_urls.discard(current_url)

            if current_url in visited_urls:
                continue

            visited_urls.add(current_url)

            await emit_progress(
                progress_callback,
                {
                    "type": "crawl_request",
                    "url": current_url,
                    "depth": depth,
                    "queue_remaining": len(queue),
                    "visited_pages": len(visited_urls),
                },
            )

            success = False
            response = None
            last_status_code = 0
            last_error = None
            last_error_category = "network"
            last_response_url = current_url
            
            for attempt in range(2):
                try:
                    response = await client.get(current_url)
                    last_response_url = str(response.url)
                    response.raise_for_status()
                    success = True
                    break
                except httpx.HTTPStatusError as exc:
                    response = exc.response
                    last_status_code = exc.response.status_code
                    last_response_url = str(exc.response.url)
                    last_error_category, _ = _describe_crawl_failure(
                        status_code=last_status_code,
                        error=exc,
                    )
                    if last_status_code in {401, 403, 404, 405, 429}:
                        break
                    await asyncio.sleep(CRAWL_RETRY_DELAY_SECONDS)
                except httpx.HTTPError as exc:
                    last_error = exc
                    last_error_category, _ = _describe_crawl_failure(error=exc)
                    await asyncio.sleep(CRAWL_RETRY_DELAY_SECONDS)
            
            if not success or response is None:
                error_category, error_detail = _describe_crawl_failure(
                    status_code=last_status_code or None,
                    error=last_error,
                )
                await emit_progress(
                    progress_callback,
                    {
                        "type": "crawl_error",
                        "url": last_response_url,
                        "depth": depth,
                        "detail": error_detail,
                        "status_code": last_status_code,
                        "category": error_category or last_error_category,
                    },
                )
                continue

            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                await emit_progress(
                    progress_callback,
                    {
                        "type": "crawl_skip",
                        "url": str(response.url),
                        "depth": depth,
                        "detail": f"Skipped non-HTML response: {content_type or 'unknown content type'}.",
                    },
                )
                continue

            page_data = _parse_page(response, depth=depth, base_domain=base_domain)
            final_url = page_data["url"]

            if final_url in page_map:
                continue

            page_map[final_url] = page_data
            pages.append(page_data)
            max_depth_reached = max(max_depth_reached, depth)
            new_links = []

            for link in page_data["internal_links"]:
                if link not in discovered_urls:
                    new_links.append(link)
                discovered_urls.add(link)

                if (
                    depth < CRAWL_MAX_DEPTH
                    and link not in visited_urls
                    and link not in queued_urls
                    and (effective_max_pages == float("inf") or len(visited_urls) < effective_max_pages)
                ):
                    queue.append((link, depth + 1))
                    queued_urls.add(link)

            await emit_progress(
                progress_callback,
                {
                    "type": "crawl_page",
                    "url": final_url,
                    "title": page_data.get("title", ""),
                    "depth": depth,
                    "page_type": page_data.get("page_type", "Other"),
                    "status_code": page_data.get("status_code", 0),
                    "analyzed_pages": len(pages),
                    "discovered_internal_pages": len(discovered_urls),
                    "queue_remaining": len(queue),
                    "internal_links_count": page_data.get("internal_links_count", 0),
                    "external_links_count": page_data.get("external_links_count", 0),
                    "new_links_count": len(new_links),
                    "new_links_sample": new_links[:3],
                },
            )

        robots_data, sitemap_data, favicon_data = await asyncio.gather(robots_task, sitemap_task, favicon_task)
        broken_link_summary = await _check_sampled_internal_links(client, pages)

        for resource_name, resource_data in (
            ("robots", robots_data),
            ("sitemap", sitemap_data),
            ("favicon", favicon_data),
        ):
            await emit_progress(
                progress_callback,
                {
                    "type": "crawl_resource",
                    "resource": resource_name,
                    "url": resource_data.get("url", ""),
                    "status": resource_data.get("status_string")
                    or (
                        f"Found ({resource_data.get('status_code', 0)})"
                        if resource_data.get("exists")
                        else "Missing"
                    ),
                },
            )

        await emit_progress(
            progress_callback,
            {
                "type": "crawl_resource",
                "resource": "broken_links",
                "status": (
                    f"{broken_link_summary.get('broken_count', 0)} broken of "
                    f"{broken_link_summary.get('checked_count', 0)} checked"
                ),
                "broken_count": broken_link_summary.get("broken_count", 0),
                "checked_count": broken_link_summary.get("checked_count", 0),
            },
        )

    declared_sitemaps = []
    for line in robots_data.get("body", "").splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("sitemap:"):
            # Safely extract the URL after the "Sitemap:" prefix (case-insensitive)
            sitemap_url = stripped[len("sitemap:"):].strip()
            if sitemap_url and sitemap_url.startswith("http"):
                declared_sitemaps.append(sitemap_url)

    primary_page = pages[0] if pages else {}
    sample_coverage_ratio = (
        round((len(pages) / len(discovered_urls)) * 100, 1)
        if discovered_urls
        else 0.0
    )

    summary = {
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
        "favicon": favicon_data,
        "declared_sitemaps": declared_sitemaps,
        "broken_link_summary": broken_link_summary,
    }

    await emit_progress(
        progress_callback,
        {
            "type": "crawl_summary",
            "analyzed_pages": summary["analyzed_pages"],
            "discovered_internal_pages": summary["discovered_internal_pages"],
            "sample_coverage_ratio": summary["sample_coverage_ratio"],
            "crawl_depth": summary["crawl_depth"],
        },
    )

    return summary
