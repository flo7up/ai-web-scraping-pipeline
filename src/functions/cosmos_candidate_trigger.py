import logging

import azure.functions as func

from src.pipeline import cosmos
from src.pipeline.config import load_config
from src.pipeline.extraction import extract_record
from src.pipeline.http_client import fetch_page
from src.pipeline.queueing import enqueue_review

bp = func.Blueprint()
logger = logging.getLogger(__name__)


@bp.cosmos_db_trigger(
    arg_name="documents",
    database_name="%COSMOS_DATABASE_NAME%",
    container_name="CandidateQueue",
    connection="CosmosDBConnection",
    lease_container_name="CandidateQueueLeases",
    create_lease_container_if_not_exists=True,
)
def cosmos_candidate_trigger(documents: func.DocumentList) -> None:
    config = load_config()
    for document in documents:
        candidate = dict(document)
        if candidate.get("status") not in {"queued", None}:
            continue
        try:
            page = fetch_page(candidate["sourceUrl"])
            record = extract_record(page.final_url, page.title, page.text, config)
            if config.quality.reviewBeforeStore:
                enqueue_review(candidate["id"], record.model_dump())
            else:
                approved = {**record.model_dump(), "status": "approved"}
                cosmos.upsert("records", approved)
            candidate["status"] = "extracted"
        except Exception as exc:
            logger.exception("Candidate processing failed: %s", exc)
            candidate["status"] = "failed"
            candidate["error"] = str(exc)
        cosmos.upsert("candidates", candidate)
