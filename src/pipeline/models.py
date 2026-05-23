from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class CandidateRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    PartitionKey: str = "candidate"
    sourceUrl: str
    discoveredFrom: str | None = None
    status: Literal["queued", "processing", "extracted", "failed"] = "queued"
    createdAt: str = Field(default_factory=utc_now_iso)
    updatedAt: str = Field(default_factory=utc_now_iso)
    error: str | None = None


class ExtractedRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    PartitionKey: str = "record"
    recordType: str
    title: str
    summary: str
    sourceUrl: str
    organization: str | None = None
    useCaseType: str | None = None
    industry: str | None = None
    technologies: list[str] = Field(default_factory=list)
    rawFields: dict[str, Any] = Field(default_factory=dict)
    status: Literal["draft", "approved", "rejected"] = "draft"
    confidence: float = 0.5
    createdAt: str = Field(default_factory=utc_now_iso)
    updatedAt: str = Field(default_factory=utc_now_iso)


class ReviewItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    PartitionKey: str = "review"
    candidateId: str
    record: dict[str, Any]
    status: Literal["queued", "approved", "rejected", "failed"] = "queued"
    createdAt: str = Field(default_factory=utc_now_iso)
    updatedAt: str = Field(default_factory=utc_now_iso)
    reasons: list[str] = Field(default_factory=list)
