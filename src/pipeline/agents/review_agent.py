import logging
from typing import Any

from src.pipeline import cosmos
from src.pipeline.config import PipelineConfig
from src.pipeline.deduplication import apply_source_identity_fields, find_duplicate_record
from src.pipeline.embeddings import apply_embedding_fields, create_record_embedding
from src.pipeline.groundedness import evaluate_groundedness
from src.pipeline.http_client import fetch_page
from src.pipeline.models import ExtractedRecord, utc_now_iso
from src.pipeline.review import review_record

logger = logging.getLogger(__name__)


def fetch_source_text(source_url: str) -> str:
    try:
        return fetch_page(source_url).text
    except Exception as exc:
        logger.warning("Groundedness source fetch failed for %s: %s: %s", source_url, type(exc).__name__, exc)
        return ""


def groundedness_score(value: dict[str, Any] | None) -> float | None:
    if not value:
        return None
    try:
        return float(value.get("score"))
    except (TypeError, ValueError):
        return None


def requeue_candidate_for_rescrape(candidate_id: str, reason: str, attempt: int) -> bool:
    candidates = cosmos.query(
        "candidates",
        "SELECT TOP 1 * FROM c WHERE c.PartitionKey = @pk AND c.id = @id",
        parameters=[{"name": "@pk", "value": "candidate"}, {"name": "@id", "value": candidate_id}],
        enable_cross_partition_query=False,
        partition_key="candidate",
    )
    if not candidates:
        return False

    candidate = candidates[0]
    candidate["status"] = "queued"
    candidate["error"] = None
    candidate["updatedAt"] = utc_now_iso()
    candidate["rescrapeAttempt"] = attempt
    candidate["rescrapeReason"] = reason
    cosmos.upsert("candidates", candidate)
    return True


def should_rescrape_for_groundedness(groundedness: dict[str, Any] | None, config: PipelineConfig) -> bool:
    score = groundedness_score(groundedness)
    return score is not None and score < config.groundedness.rescrapeBelowScore


def review_item(item: dict[str, Any], config: PipelineConfig) -> dict[str, Any]:
    if item.get("status") not in {"queued", None}:
        return item

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
            source_text = fetch_source_text(record.sourceUrl)
            groundedness = evaluate_groundedness(record_data, source_text, config)
            record_data["groundedness"] = groundedness
            if should_rescrape_for_groundedness(groundedness, config):
                retry_count = int(item.get("scrapeRetryCount") or 0)
                score = groundedness_score(groundedness)
                reason = (
                    f"Groundedness score {score:g} is below {config.groundedness.rescrapeBelowScore:g}; "
                    "repeating scrape and extraction."
                )
                if retry_count < config.groundedness.maxRescrapeAttempts:
                    next_attempt = retry_count + 1
                    if requeue_candidate_for_rescrape(item["candidateId"], reason, next_attempt):
                        item["duplicateReview"] = duplicate_review or {"status": "unique"}
                        item["groundedness"] = groundedness
                        item["scrapeRetryCount"] = next_attempt
                        item["reasons"] = reasons + [reason]
                        item["status"] = "retrying"
                        item["updatedAt"] = utc_now_iso()
                        return item
                    approved = False
                    reasons.append(f"{reason} Candidate {item['candidateId']} could not be requeued.")
                else:
                    approved = False
                    reasons.append(
                        f"Groundedness score {score:g} remained below {config.groundedness.rescrapeBelowScore:g} "
                        f"after {retry_count} rescrape attempt(s)."
                    )
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
        item["status"] = "failed"
        item["reasons"] = [str(exc)]
        raise
    finally:
        cosmos.upsert("review", item)

    return item
