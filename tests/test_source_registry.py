from src.pipeline.source_registry import source_page_id


def test_source_page_id_hashes_url_for_cosmos_id_safety():
    value = source_page_id("https://example.com/path")
    assert len(value) == 64
    assert "/" not in value
    assert value == source_page_id("HTTPS://EXAMPLE.COM/path")
