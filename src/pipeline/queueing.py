from . import cosmos
from .models import CandidateRecord, ReviewItem


def enqueue_candidate(url: str, discovered_from: str | None = None) -> CandidateRecord:
    candidate = CandidateRecord(sourceUrl=url, discoveredFrom=discovered_from)
    cosmos.upsert("candidates", candidate.model_dump())
    return candidate


def enqueue_review(candidate_id: str, record: dict) -> ReviewItem:
    item = ReviewItem(candidateId=candidate_id, record=record)
    cosmos.upsert("review", item.model_dump())
    return item
