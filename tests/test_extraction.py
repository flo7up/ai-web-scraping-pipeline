from src.pipeline.config import PipelineConfig
from src.pipeline.extraction import deterministic_extract, llm_extract


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


def test_llm_extract_normalizes_null_model_fields(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "test-deployment")

    def fake_chat_json(*args, **kwargs):
        return {
            "title": "Example Domain",
            "summary": "A public example domain.",
            "sourceUrl": None,
            "technologies": None,
            "confidence": "high",
            "rawFields": None,
        }

    monkeypatch.setattr("src.pipeline.extraction.chat_json", fake_chat_json)

    record = llm_extract(
        url="https://example.com",
        title="Example Domain",
        text="Example Domain is used for examples.",
        config=PipelineConfig(recordType="case"),
    )

    assert record is not None
    assert record.sourceUrl == "https://example.com"
    assert record.technologies == []
    assert record.confidence == 0.85
    assert record.rawFields["extractionMode"] == "llm"
