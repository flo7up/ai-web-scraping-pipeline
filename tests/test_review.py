from src.pipeline.config import PipelineConfig, SchemaConfig, SchemaField
from src.pipeline.models import ExtractedRecord
from src.pipeline.review import review_record


def test_review_requires_configured_fields():
    config = PipelineConfig(recordSchema=SchemaConfig(fields=[SchemaField(name="title", required=True)]))
    record = ExtractedRecord(recordType="case", title="", summary="summary", sourceUrl="https://example.com")
    approved, reasons = review_record(record, config)
    assert approved is False
    assert "Missing required field: title" in reasons


def test_review_accepts_valid_record():
    config = PipelineConfig(recordSchema=SchemaConfig(fields=[SchemaField(name="title", required=True)]))
    record = ExtractedRecord(recordType="case", title="A title", summary="summary", sourceUrl="https://example.com")
    approved, reasons = review_record(record, config)
    assert approved is True
    assert reasons == []
