import hashlib
import logging
import re
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from . import cosmos
from .config import PipelineConfig
from .models import ExtractedRecord

logger = logging.getLogger(__name__)

TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_NAMES = {"fbclid", "gclid", "msclkid"}


def normalize_source_url(url: str | None) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_QUERY_NAMES and not key.lower().startswith(TRACKING_QUERY_PREFIXES)
    ]
    normalized_path = parsed.path.rstrip("/") or "/"
    return urlunparse(
        (
            parsed.scheme.lower() or "https",
            parsed.netloc.lower(),
            normalized_path,
            "",
            urlencode(sorted(query_pairs)),
            "",
        )
    )


def source_url_hash(url: str | None) -> str:
    normalized = normalize_source_url(url)
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def apply_source_identity_fields(record: dict[str, Any]) -> dict[str, Any]:
    normalized_url = normalize_source_url(record.get("sourceUrl"))
    if normalized_url:
        record["normalizedSourceUrl"] = normalized_url
        record["sourceUrlHash"] = source_url_hash(normalized_url)
    return record


def normalize_match_text(value: Any) -> str:
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    if isinstance(value, dict):
        value = " ".join(str(item) for item in value.values())
    text = str(value or "").lower()
    text = re.sub(r"[^a-z0-9+#.]+", " ", text)
    return " ".join(text.split())


def token_overlap(left: Any, right: Any) -> float:
    left_tokens = {token for token in normalize_match_text(left).split() if len(token) > 2}
    right_tokens = {token for token in normalize_match_text(right).split() if len(token) > 2}
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens.intersection(right_tokens)) / max(len(left_tokens), len(right_tokens))


def text_similarity(left: Any, right: Any) -> float:
    left_text = normalize_match_text(left)
    right_text = normalize_match_text(right)
    if not left_text or not right_text:
        return 0.0
    return SequenceMatcher(None, left_text, right_text).ratio()


def to_similarity_score(vector_distance: Any) -> float | None:
    try:
        distance = float(vector_distance)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, 1.0 - distance))


def find_exact_source_candidates(record: dict[str, Any]) -> list[dict[str, Any]]:
    normalized_url = normalize_source_url(record.get("sourceUrl"))
    hash_value = source_url_hash(normalized_url)
    if not normalized_url and not hash_value:
        return []

    query = """
    SELECT TOP 5 c.id, c.title, c.summary, c.sourceUrl, c.normalizedSourceUrl, c.sourceUrlHash,
        c.organization, c.useCaseType, c.industry, c.technologies
    FROM c
    WHERE c.PartitionKey = 'record'
    AND c.id != @id
    AND (
        c.sourceUrl = @sourceUrl
        OR c.sourceUrl = @normalizedSourceUrl
        OR c.normalizedSourceUrl = @normalizedSourceUrl
        OR c.sourceUrlHash = @sourceUrlHash
    )
    """
    return cosmos.query(
        "records",
        query,
        parameters=[
            {"name": "@id", "value": record.get("id")},
            {"name": "@sourceUrl", "value": record.get("sourceUrl")},
            {"name": "@normalizedSourceUrl", "value": normalized_url},
            {"name": "@sourceUrlHash", "value": hash_value},
        ],
        enable_cross_partition_query=True,
    )


def find_vector_candidates(record: dict[str, Any], embedding: list[float], config: PipelineConfig) -> list[dict[str, Any]]:
    if not embedding:
        return []

    limit = max(1, min(config.quality.duplicateCandidateLimit, 20))
    query = f"""
    SELECT TOP {limit} c.id, c.title, c.summary, c.sourceUrl, c.normalizedSourceUrl, c.sourceUrlHash,
        c.organization, c.useCaseType, c.industry, c.technologies,
        VectorDistance(c.embedding, @embedding) AS vectorDistance
    FROM c
    WHERE c.PartitionKey = 'record'
    AND c.id != @id
    AND IS_DEFINED(c.embedding)
    ORDER BY VectorDistance(c.embedding, @embedding)
    """
    try:
        return cosmos.query(
            "records",
            query,
            parameters=[
                {"name": "@id", "value": record.get("id")},
                {"name": "@embedding", "value": embedding},
            ],
            enable_cross_partition_query=True,
        )
    except Exception as exc:
        logger.warning("Vector duplicate lookup failed: %s: %s", type(exc).__name__, exc)
        return []


def calculate_duplicate_signals(record: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    normalized_url = normalize_source_url(record.get("sourceUrl"))
    hash_value = source_url_hash(normalized_url)
    candidate_url = candidate.get("normalizedSourceUrl") or normalize_source_url(candidate.get("sourceUrl"))
    candidate_hash = candidate.get("sourceUrlHash") or source_url_hash(candidate_url)
    exact_source_match = bool(normalized_url and candidate_url and normalized_url == candidate_url) or bool(
        hash_value and candidate_hash and hash_value == candidate_hash
    )

    similarity_score = to_similarity_score(candidate.get("vectorDistance"))
    title_similarity = text_similarity(record.get("title"), candidate.get("title"))
    organization_overlap = token_overlap(record.get("organization"), candidate.get("organization"))
    content_overlap = max(
        token_overlap(record.get("summary"), candidate.get("summary")),
        token_overlap(record.get("useCaseType"), candidate.get("useCaseType")),
    )
    technology_overlap = token_overlap(record.get("technologies"), candidate.get("technologies"))

    if exact_source_match:
        confidence = 0.99
    else:
        confidence = 0.0
        confidence += (similarity_score or 0.0) * 0.5
        confidence += title_similarity * 0.2
        confidence += organization_overlap * 0.15
        confidence += content_overlap * 0.1
        confidence += technology_overlap * 0.05

    reasons = []
    if exact_source_match:
        reasons.append("same source URL")
    if similarity_score is not None:
        reasons.append("semantic vector similarity")
    if title_similarity >= 0.8:
        reasons.append("similar title")
    if organization_overlap >= 0.8:
        reasons.append("same organization")
    if content_overlap >= 0.65:
        reasons.append("similar content")

    return {
        "confidence": round(min(confidence, 1.0), 4),
        "exactSourceMatch": exact_source_match,
        "vectorDistance": round(float(candidate["vectorDistance"]), 6) if candidate.get("vectorDistance") is not None else None,
        "similarityScore": round(similarity_score, 6) if similarity_score is not None else None,
        "titleSimilarity": round(title_similarity, 4),
        "organizationOverlap": round(organization_overlap, 4),
        "contentOverlap": round(content_overlap, 4),
        "technologyOverlap": round(technology_overlap, 4),
        "reasons": reasons,
    }


def decorate_candidate(record: dict[str, Any], candidate: dict[str, Any], source: str) -> dict[str, Any]:
    candidate = dict(candidate)
    candidate["candidateSource"] = source
    candidate["duplicateSignals"] = calculate_duplicate_signals(record, candidate)
    return candidate


def build_duplicate_decision(candidate: dict[str, Any], config: PipelineConfig) -> dict[str, Any] | None:
    signals = candidate.get("duplicateSignals", {})
    exact_source_match = bool(signals.get("exactSourceMatch"))
    strong_semantic_match = bool(
        signals.get("similarityScore") is not None
        and signals["similarityScore"] >= config.quality.duplicateSimilarityThreshold
        and max(signals.get("titleSimilarity", 0.0), signals.get("organizationOverlap", 0.0), signals.get("contentOverlap", 0.0))
        >= 0.65
    )
    enough_confidence = signals.get("confidence", 0.0) >= config.quality.duplicateConfidenceThreshold

    if exact_source_match:
        reason = "Exact normalized source URL or source URL hash already exists."
    elif strong_semantic_match and enough_confidence:
        reason = "Strong embedding similarity plus matching title, organization, or content signals."
    else:
        return None

    return {
        "status": "duplicate",
        "matchedRecordId": candidate.get("id"),
        "confidence": signals.get("confidence", 0.0),
        "reason": reason,
        "signals": signals,
    }


def find_duplicate_record(
    record: ExtractedRecord | dict[str, Any], config: PipelineConfig, embedding: list[float] | None = None
) -> dict[str, Any] | None:
    if not config.quality.duplicateDetection:
        return None

    payload = record.model_dump() if isinstance(record, ExtractedRecord) else dict(record)
    exact_candidates = [decorate_candidate(payload, item, "source-url") for item in find_exact_source_candidates(payload)]
    vector_candidates = [
        decorate_candidate(payload, item, "vector") for item in find_vector_candidates(payload, embedding or [], config)
    ]
    candidates = sorted(
        exact_candidates + vector_candidates,
        key=lambda item: (
            item.get("duplicateSignals", {}).get("confidence", 0.0),
            item.get("duplicateSignals", {}).get("similarityScore") or 0.0,
        ),
        reverse=True,
    )

    for candidate in candidates:
        decision = build_duplicate_decision(candidate, config)
        if decision:
            return decision
    return None