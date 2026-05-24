from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.pipeline.config import PipelineConfig
from src.pipeline.http_client import fetch_page
from src.pipeline.models import CandidateRecord
from src.pipeline.queueing import enqueue_candidate
from src.pipeline.source_registry import mark_source_visited, upsert_source_page

YANDEX_SEARCH_URL = "https://yandex.eu/search/"
YANDEX_SEARCH_URLS = (YANDEX_SEARCH_URL, "https://yandex.com/search/", "https://yandex.ru/search/")
YANDEX_HOST_SUFFIXES = ("yandex.com", "yandex.eu", "yandex.ru")
YANDEX_INTERNAL_HOST_MARKERS = ("yandex.", "yandexcloud.")
SEARCH_USER_AGENT = "ai-web-scraping-pipeline/0.1"


def is_allowed_url(url: str, allowed_domains: list[str], blocked_domains: list[str]) -> bool:
    hostname = (urlparse(url).hostname or "").lower()
    if any(hostname.endswith(domain.lower()) for domain in blocked_domains):
        return False
    return not allowed_domains or any(hostname.endswith(domain.lower()) for domain in allowed_domains)


def _unwrap_yandex_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.netloc.endswith(YANDEX_HOST_SUFFIXES):
        return url

    query = parse_qs(parsed.query)
    for key in ("url", "u", "target"):
        if query.get(key):
            return unquote(query[key][0])
    return url


def extract_yandex_result_urls(html: str, base_url: str = YANDEX_SEARCH_URL, limit: int = 10) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    results: list[str] = []
    for anchor in soup.find_all("a", href=True):
        absolute = urljoin(base_url, anchor["href"])
        unwrapped = _unwrap_yandex_url(absolute)
        parsed = urlparse(unwrapped)
        if parsed.scheme not in {"http", "https"}:
            continue
        hostname = (parsed.hostname or "").lower()
        if parsed.netloc.endswith(YANDEX_HOST_SUFFIXES) or any(marker in hostname for marker in YANDEX_INTERNAL_HOST_MARKERS):
            continue
        normalized = parsed._replace(fragment="").geturl()
        if normalized not in results:
            results.append(normalized)
        if len(results) >= limit:
            break
    return results


def yandex_search(query: str, limit: int = 10, timeout: int = 20) -> list[str]:
    last_error: Exception | None = None
    for search_url in YANDEX_SEARCH_URLS:
        try:
            response = requests.get(
                search_url,
                params={"text": query},
                timeout=timeout,
                headers={"User-Agent": SEARCH_USER_AGENT},
            )
            response.raise_for_status()
            return extract_yandex_result_urls(response.text, response.url, limit=limit)
        except requests.RequestException as exc:
            last_error = exc
    if last_error:
        raise last_error
    return []


def _enqueue_if_allowed(
    link: str,
    discovered_from: str,
    config: PipelineConfig,
    queued: list[CandidateRecord],
    max_links: int,
) -> None:
    if len(queued) >= max_links:
        return
    if not is_allowed_url(link, config.sourceDiscovery.allowedDomains, config.sourceDiscovery.blockedDomains):
        return
    queued.append(enqueue_candidate(link, discovered_from=discovered_from))


def screen_sources(
    source_urls: list[str],
    max_links: int,
    config: PipelineConfig,
    search_queries: list[str] | None = None,
    search_provider: str | None = None,
) -> list[CandidateRecord]:
    queued: list[CandidateRecord] = []

    for source_url in source_urls:
        if len(queued) >= max_links:
            break
        upsert_source_page(source_url, config.sourceDiscovery.revisitFrequencyDays)
        page = fetch_page(source_url)
        for link in page.links:
            if len(queued) >= max_links:
                break
            _enqueue_if_allowed(link, source_url, config, queued, max_links)
        mark_source_visited(source_url, config.sourceDiscovery.revisitFrequencyDays)

    provider = search_provider or config.sourceDiscovery.searchProvider
    queries = config.sourceDiscovery.searchQueries if search_queries is None else search_queries
    if provider == "yandex":
        for query in queries:
            if len(queued) >= max_links:
                break
            for link in yandex_search(query, limit=config.sourceDiscovery.searchMaxResults):
                _enqueue_if_allowed(link, f"yandex:{query}", config, queued, max_links)
                if len(queued) >= max_links:
                    break

    return queued
