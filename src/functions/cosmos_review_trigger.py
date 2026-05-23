import logging

import azure.functions as func

from src.pipeline import cosmos
from src.pipeline.config import load_config
from src.pipeline.deduplication import apply_source_identity_fields, find_duplicate_record
from src.pipeline.embeddings import apply_embedding_fields, create_record_embedding
from src.pipeline.groundedness import evaluate_groundedness
from src.pipeline.http_client import fetch_page
from src.pipeline.models import ExtractedRecord
from src.pipeline.review import review_record

bp = func.Blueprint()
logger = logging.getLogger(__name__)


def _fetch_source_text(source_url: str) -> str:
    try:
        return fetch_page(source_url).text
    except Exception as exc:
        logger.warning("Groundedness source fetch failed for %s: %s: %s", source_url, type(exc).__name__, exc)
        return ""


@bp.cosmos_db_trigger(
    arg_name="documents",
    database_name="%COSMOS_DATABASE_NAME%",
    container_name="ReviewQueue",
    connection="CosmosDBConnection",
    lease_container_name="ReviewQueueLeases",
    create_lease_container_if_not_exists=True,
)
def cosmos_review_trigger(documents: func.DocumentList) -> None:
    config = load_config()
    for document in documents:
        item = dict(document)
        if item.get("status") not in {"queued", None}:
            continue
        try:
            record = ExtractedRecord.model_validate(item["record"])
            approved, reasons = review_record(record, config)
            record_data = apply_source_identity_fields(record.model_dump())

            embedding = create_record_embedding(record, config)
            record_data = apply_embedding_fields(record_data, embedding, config)

            duplicate_review = None
            if approved:
                duplicate_review = find_duplicate_record(record_data, config, embedding=embedding)
                if duplicate_review:
                    approved = False
                    reasons.append(f"Duplicate record: {duplicate_review['reason']}")

            groundedness = None
            if approved:
                source_text = _fetch_source_text(record.sourceUrl)
                groundedness = evaluate_groundedness(record_data, source_text, config)
                record_data["groundedness"] = groundedness
                if config.groundedness.requirePass and groundedness.get("passed") is False:
                    approved = False
                    reasons.append(f"Groundedness check failed: {groundedness.get('reason')}")

            item["duplicateReview"] = duplicate_review or {"status": "unique" if approved else "not_checked"}
            if groundedness:
                item["groundedness"] = groundedness
            item["reasons"] = reasons
            item["status"] = "approved" if approved else "rejected"
            if approved:
                cosmos.upsert("records", {**record_data, "status": "approved"})
        except Exception as exc:
            logger.exception("Review failed: %s", exc)
            item["status"] = "failed"
            item["reasons"] = [str(exc)]
        cosmos.upsert("review", item)
