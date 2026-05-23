import json
import logging

import azure.functions as func

from src.pipeline.config import load_config
from src.pipeline.http_client import fetch_page
from src.pipeline.queueing import enqueue_candidate
from src.pipeline.source_registry import due_source_pages, mark_source_visited

bp = func.Blueprint()
logger = logging.getLogger(__name__)


@bp.timer_trigger(schedule="%SOURCE_REFRESH_CRON%", arg_name="timer", run_on_startup=False, use_monitor=True)
def timer_source_refresh(timer: func.TimerRequest) -> None:
    config = load_config()
    for source in due_source_pages(limit=10):
        try:
            page = fetch_page(source["url"])
            for link in page.links[: config.sourceDiscovery.maxLinksPerSource]:
                enqueue_candidate(link, discovered_from=source["url"])
            mark_source_visited(source["url"], config.sourceDiscovery.revisitFrequencyDays)
        except Exception as exc:
            logger.exception("Scheduled source refresh failed for %s: %s", json.dumps(source), exc)
