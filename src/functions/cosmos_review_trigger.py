import logging

import azure.functions as func

from src.pipeline import cosmos
from src.pipeline.config import load_config
from src.pipeline.models import ExtractedRecord
from src.pipeline.review import review_record

bp = func.Blueprint()
logger = logging.getLogger(__name__)


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
            item["reasons"] = reasons
            item["status"] = "approved" if approved else "rejected"
            if approved:
                cosmos.upsert("records", {**record.model_dump(), "status": "approved"})
        except Exception as exc:
            logger.exception("Review failed: %s", exc)
            item["status"] = "failed"
            item["reasons"] = [str(exc)]
        cosmos.upsert("review", item)
