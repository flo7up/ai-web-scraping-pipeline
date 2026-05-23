from .config import PipelineConfig
from .models import ExtractedRecord


def review_record(record: ExtractedRecord, config: PipelineConfig) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    payload = record.model_dump()

    for field in config.recordSchema.fields:
        if not field.required:
            continue
        value = payload.get(field.name) or record.rawFields.get(field.name)
        if value in (None, "", []):
            reasons.append(f"Missing required field: {field.name}")

    if config.quality.requireSourceEvidence and not record.sourceUrl:
        reasons.append("Missing source URL")

    return not reasons, reasons
