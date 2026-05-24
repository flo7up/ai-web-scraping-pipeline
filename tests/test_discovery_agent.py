from src.pipeline.agents.discovery_agent import extract_yandex_result_urls, is_allowed_url
from src.pipeline.config import PipelineConfig, SourceDiscoveryConfig


def test_extract_yandex_result_urls_skips_internal_links_and_unwraps_redirects():
    html = """
    <a href="/search/?text=test">internal</a>
    <a href="https://yandex.cloud/en/services/smartcaptcha">captcha</a>
    <a href="https://yandex.com/clck/jsredir?url=https%3A%2F%2Fexample.com%2Fcase%23section">result</a>
    <a href="https://example.org/other">other</a>
    <a href="https://example.com/case">duplicate normalized</a>
    """
    results = extract_yandex_result_urls(html, limit=5)
    assert results == ["https://example.com/case", "https://example.org/other"]


def test_allowed_url_respects_allow_and_block_lists():
    config = PipelineConfig(
        sourceDiscovery=SourceDiscoveryConfig(
            allowedDomains=["example.com"],
            blockedDomains=["blocked.example.com"],
        )
    )
    assert is_allowed_url("https://news.example.com/case", config.sourceDiscovery.allowedDomains, config.sourceDiscovery.blockedDomains)
    assert not is_allowed_url("https://blocked.example.com/case", config.sourceDiscovery.allowedDomains, config.sourceDiscovery.blockedDomains)
    assert not is_allowed_url("https://example.org/case", config.sourceDiscovery.allowedDomains, config.sourceDiscovery.blockedDomains)
