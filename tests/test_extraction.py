from src.pipeline.config import PipelineConfig
from src.pipeline.extraction import deterministic_extract


def test_deterministic_extract_returns_record():
    record = deterministic_extract(
        url="https://example.com/case-study",
        title="Example case study",
        text="Example Corp uses automation to process support requests. More text follows.",
        config=PipelineConfig(recordType="case"),
    )
    assert record.title == "Example case study"
    assert record.sourceUrl == "https://example.com/case-study"
    assert record.recordType == "case"
    assert record.rawFields["extractionMode"] == "deterministic"
