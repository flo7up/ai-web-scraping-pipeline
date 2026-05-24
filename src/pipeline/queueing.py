from . import cosmos
from .models import CandidateRecord, ReviewItem, utc_now_iso


def enqueue_candidate(url: str, discovered_from: str | None = None) -> CandidateRecord:
    candidate = CandidateRecord(sourceUrl=url, discoveredFrom=discovered_from)
    cosmos.upsert("candidates", candidate.model_dump())
    return candidate


def enqueue_review(candidate_id: str, record: dict) -> ReviewItem:
    review_id = f"review-{candidate_id}"
    existing = cosmos.query(
        "review",
        "SELECT TOP 1 * FROM c WHERE c.PartitionKey = @pk AND c.id = @id",
        parameters=[{"name": "@pk", "value": "review"}, {"name": "@id", "value": review_id}],
        enable_cross_partition_query=False,
        partition_key="review",
    )
    if existing:
        existing_item = existing[0]
        if existing_item.get("status") in {"retrying", "failed"}:
            existing_item["record"] = record
            existing_item["status"] = "queued"
            existing_item["reasons"] = []
            existing_item["groundedness"] = None
            existing_item["duplicateReview"] = None
            existing_item["updatedAt"] = utc_now_iso()
            cosmos.upsert("review", existing_item)
            return ReviewItem.model_validate(existing_item)
        return ReviewItem.model_validate(existing[0])

    item = ReviewItem(id=review_id, candidateId=candidate_id, record=record)
    cosmos.upsert("review", item.model_dump())
    return item
