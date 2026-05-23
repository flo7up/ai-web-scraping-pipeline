import json
import logging
from urllib.parse import urlparse

import azure.functions as func

from src.pipeline.config import load_config
from src.pipeline.http_client import fetch_page
from src.pipeline.queueing import enqueue_candidate
from src.pipeline.source_registry import mark_source_visited, upsert_source_page

bp = func.Blueprint()
logger = logging.getLogger(__name__)


def _allowed(url: str, allowed_domains: list[str], blocked_domains: list[str]) -> bool:
    hostname = (urlparse(url).hostname or "").lower()
    if any(hostname.endswith(domain.lower()) for domain in blocked_domains):
        return False
    return not allowed_domains or any(hostname.endswith(domain.lower()) for domain in allowed_domains)


@bp.route(route="screen-sources", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def http_screen_sources(req: func.HttpRequest) -> func.HttpResponse:
    try:
        config = load_config()
        body = req.get_json() if req.get_body() else {}
        urls = body.get("urls") or config.sourceDiscovery.seedUrls
        max_links = int(body.get("maxLinks") or config.sourceDiscovery.maxLinksPerSource)
        queued = []

        for source_url in urls:
            upsert_source_page(source_url, config.sourceDiscovery.revisitFrequencyDays)
            page = fetch_page(source_url)
            for link in page.links:
                if len(queued) >= max_links:
                    break
                if not _allowed(link, config.sourceDiscovery.allowedDomains, config.sourceDiscovery.blockedDomains):
                    continue
                queued.append(enqueue_candidate(link, discovered_from=source_url).model_dump())
            mark_source_visited(source_url, config.sourceDiscovery.revisitFrequencyDays)

        return func.HttpResponse(json.dumps({"queued": queued, "count": len(queued)}), mimetype="application/json")
    except Exception as exc:
        logger.exception("Source screening failed: %s", exc)
        return func.HttpResponse(json.dumps({"error": str(exc)}), status_code=500, mimetype="application/json")
