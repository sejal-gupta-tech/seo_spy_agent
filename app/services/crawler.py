import asyncio
import json
import re
import time
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
from app.core.logger import logger
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

# Maximum size for HTML bodies (2.5 MB) to prevent MemoryError
MAX_HTML_BODY_SIZE = 2500000 


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
    """Extract word count efficiently by filtering text nodes and checking ancestors."""
    # Define tags to exclude from word count
    exclude_tags = {"script", "style", "noscript", "svg", "header", "footer", "nav", "head", "form"}
    
    # Get all text nodes
    texts = soup.find_all(string=True)
    visible_texts = []
    
    for t in texts:
        content = str(t).strip()
        if not content:
            continue
            
        parent = t.parent
        if not parent:
            continue
            
        # Recursive check up the tree to see if any ancestor is excluded
        is_excluded = False
        curr = parent
        while curr and curr.name != '[document]':
            if curr.name in exclude_tags:
                is_excluded = True
                break
            # Also check for hidden elements if style attribute exists
            if curr.has_attr('style'):
                style = str(curr.get('style', '')).lower()
                if 'display: none' in style or 'visibility: hidden' in style:
                    is_excluded = True
                    break
            curr = curr.parent
            
        if not is_excluded:
            visible_texts.append(content)
    
    combined_text = " ".join(visible_texts)
    # Match words including those with hyphens and apostrophes
    words = re.findall(r"\b[\w'-]+\b", combined_text)
    
    count = len(words)
    
    # Fallback: if we found 0 words but the body has text, try a simpler get_text()
    if count == 0 and soup.body:
        fallback_text = soup.body.get_text(separator=" ", strip=True)
        fallback_words = re.findall(r"\b[\w'-]+\b", fallback_text)
        count = len(fallback_words)
        
    return count


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


def _analyze_page_favicon(soup: BeautifulSoup, final_url: str) -> dict:
    """Robust favicon detection."""
    icon_tags = soup.find_all("link", rel=lambda x: x and any("icon" in str(r).lower() for r in (x if isinstance(x, list) else [x])))
    
    best_favicon = None
    
    for tag in icon_tags:
        rel = [str(r).lower() for r in (tag.get("rel", []) if isinstance(tag.get("rel"), list) else [tag.get("rel")])]
        href = tag.get("href", "").strip()
        
        if not href or href.startswith("data:"):
            continue
            
        absolute_url = urljoin(final_url, href)
        
        priority = 3
        if any("apple-touch-icon" in r for r in rel):
            priority = 1
        elif any("icon" in r for r in rel) and not any("shortcut" in r for r in rel):
            priority = 2
        elif any("shortcut" in r for r in rel):
            priority = 4
            
        if best_favicon is None or priority < best_favicon["priority"]:
            best_favicon = {
                "url": absolute_url,
                "priority": priority,
                "source": "html"
            }

    if best_favicon:
        return {
            "status": "Present",
            "url": best_favicon["url"],
            "source": "html"
        }

    return {
        "status": "Missing",
        "url": "",
        "source": "html"
    }


def _parse_page_from_text(html_text: str, url: str, status_code: int, depth: int, base_domain: str) -> dict:
    soup = BeautifulSoup(html_text, "lxml")
    final_url = normalize_crawl_url(url)

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

    favicon_data = _analyze_page_favicon(soup, url)

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
        "status_code": status_code,
        "title": title,
        "title_length": len(title),
        "description": description,
        "meta_description_length": len(description),
        "canonical_url": canonical_href,
        "has_canonical": bool(canonical_href),
        "favicon": favicon_data,
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

def _parse_page(response: httpx.Response, depth: int, base_domain: str) -> dict:
    return _parse_page_from_text(response.text, str(response.url), response.status_code, depth, base_domain)


async def _fetch_favicon(client: httpx.AsyncClient, target_url: str) -> dict:
    """Fallback favicon detection."""
    try:
        async with client.stream("GET", target_url, headers=CRAWL_HEADERS, follow_redirects=True) as response:
            if response.status_code != 200:
                return {"status": "Missing", "url": "", "source": "fallback"}
                
            content_type = response.headers.get("content-type", "").lower().split(";")[0].strip()
            is_image = "image/" in content_type
            
            if is_image:
                return {
                    "status": "Present",
                    "url": str(response.url),
                    "source": "fallback"
                }
    except Exception:
        pass

    return {
        "status": "Missing",
        "url": "",
        "source": "fallback"
    }

async def _fetch_robots_txt(client: httpx.AsyncClient, target_url: str) -> dict:
    try:
        async with client.stream("GET", target_url, headers=CRAWL_HEADERS, follow_redirects=True) as response:
            content_type = response.headers.get("content-type", "").lower()
            
            # Read first 1MB of robots.txt max
            body_parts = []
            total_read = 0
            async for chunk in response.aiter_bytes():
                body_parts.append(chunk)
                total_read += len(chunk)
                if total_read > 1000000: break
            
            body = b"".join(body_parts).decode(response.encoding or "utf-8", errors="replace")
            
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
            elif "text/plain" not in content_type and response.status_code == 200:
                # Some sites serve robots with wrong content-type but it's still robots
                if any(x in body.lower() for x in ["user-agent", "disallow", "allow"]):
                    status = "Found (Valid, but wrong Content-Type)"
                    exists = True
                else:
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
        async with client.stream("GET", target_url, headers=CRAWL_HEADERS, follow_redirects=True) as response:
            content_type = response.headers.get("content-type", "").lower()
            
            # Read first 2MB of sitemap max
            body_parts = []
            total_read = 0
            async for chunk in response.aiter_bytes():
                body_parts.append(chunk)
                total_read += len(chunk)
                if total_read > 2000000: break
            
            body = b"".join(body_parts).decode(response.encoding or "utf-8", errors="replace")

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
            elif "xml" not in content_type and "<urlset" not in body.lower() and "<sitemapindex" not in body.lower():
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

    _configured_max = max_pages if max_pages is not None else CRAWL_MAX_PAGES
    effective_max_pages = _configured_max if _configured_max > 0 else float("inf")
    display_max_pages = _configured_max if _configured_max > 0 else 9999

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
        robots_task = asyncio.create_task(_fetch_robots_txt(client, urljoin(normalized_start_url, "/robots.txt")))
        sitemap_task = asyncio.create_task(_fetch_sitemap_xml(client, urljoin(normalized_start_url, "/sitemap.xml")))
        favicon_task = asyncio.create_task(_fetch_favicon(client, urljoin(normalized_start_url, "/favicon.ico")))

        queue = asyncio.Queue()
        await queue.put((normalized_start_url, 0))
        
        visited_urls = set()
        discovered_urls = {normalized_start_url}
        pages = []
        page_map = {}
        
        semaphore = asyncio.Semaphore(5)
        
        async def worker(worker_id: int):
            last_heartbeat = time.time()
            while not queue.empty() or queue.qsize() > 0:
                # Periodic heartbeat to keep the frontend updated during long crawls
                if time.time() - last_heartbeat > 5.0:
                    await emit_progress(progress_callback, {
                        "type": "heartbeat", "worker": worker_id, 
                        "visited": len(visited_urls), "queued": queue.qsize()
                    })
                    last_heartbeat = time.time()

                try:
                    current_url, depth = await asyncio.wait_for(queue.get(), timeout=1.5)
                except asyncio.TimeoutError:
                    break
                
                if current_url in visited_urls or len(pages) >= effective_max_pages:
                    queue.task_done()
                    continue
                    
                visited_urls.add(current_url)
                
                async with semaphore:
                    try:
                        await emit_progress(progress_callback, {
                            "type": "crawl_request", "url": current_url, "depth": depth,
                            "visited_pages": len(visited_urls)
                        })
                        
                        # Use streaming to avoid MemoryError on large responses
                        async with client.stream("GET", current_url, follow_redirects=True, timeout=10.0) as response:
                            if response.status_code >= 400:
                                await response.aread() # Drain briefly
                                queue.task_done()
                                continue

                            content_type = response.headers.get("content-type", "").lower()
                            if "text/html" not in content_type:
                                queue.task_done()
                                continue

                            # Check content length if available
                            content_length = response.headers.get("content-length")
                            if content_length and int(content_length) > MAX_HTML_BODY_SIZE:
                                logger.warning(f"Skipping {current_url} - Size {content_length} exceeds limit")
                                queue.task_done()
                                continue

                            body_parts = []
                            total_read = 0
                            async for chunk in response.aiter_bytes():
                                body_parts.append(chunk)
                                total_read += len(chunk)
                                if total_read > MAX_HTML_BODY_SIZE:
                                    logger.warning(f"Truncating {current_url} - exceeds limit")
                                    break
                            
                            html_text = b"".join(body_parts).decode(response.encoding or "utf-8", errors="replace")
                            
                            page_data = _parse_page_from_text(html_text, str(response.url), response.status_code, depth, base_domain)
                            final_url = page_data["url"]
                            
                            if final_url not in page_map:
                                page_map[final_url] = page_data
                                pages.append(page_data)
                                
                                for link in page_data["internal_links"]:
                                    if link not in discovered_urls and depth < CRAWL_MAX_DEPTH:
                                        discovered_urls.add(link)
                                        await queue.put((link, depth + 1))
                                        
                                await emit_progress(progress_callback, {
                                    "type": "crawl_page", "url": final_url, "title": page_data.get("title", ""),
                                    "depth": depth, "status_code": page_data.get("status_code", 0),
                                    "analyzed_pages": len(pages), "discovered_internal_pages": len(discovered_urls)
                                })
                    except Exception as e:
                        logger.error(f"Crawl error for {current_url}: {e}")
                
                queue.task_done()

        # Run multiple workers for high-concurrency crawling
        await asyncio.gather(*(worker(i) for i in range(5)))

        robots_data, sitemap_data, favicon_data = await asyncio.gather(robots_task, sitemap_task, favicon_task)
        broken_link_summary = await _check_sampled_internal_links(client, pages)

        for resource_name, resource_data in (("robots", robots_data), ("sitemap", sitemap_data), ("favicon", favicon_data)):
            await emit_progress(progress_callback, {
                "type": "crawl_resource", "resource": resource_name, "url": resource_data.get("url", ""),
                "status": resource_data.get("status_string") or ("Found" if resource_data.get("exists") else "Missing")
            })

        return {
            "pages": pages, "robots": robots_data, "sitemap": sitemap_data, "favicon": favicon_data,
            "discovered_internal_pages": len(discovered_urls), "crawl_depth": CRAWL_MAX_DEPTH,
            "sample_coverage_ratio": (len(pages) / len(discovered_urls)) if discovered_urls else 0,
            "broken_internal_link_ratio": broken_link_summary.get("broken_ratio", 0.0),
            "broken_links": broken_link_summary.get("broken_links", [])
        }
