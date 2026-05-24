from src.pipeline import llm


def test_chat_json_uses_agent_framework_when_project_endpoint_is_configured(monkeypatch):
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://example.services.ai.azure.com/api/projects/project")
    captured = {}

    def fake_run_agent_json(agent_name, instructions, prompt, deployment, tools=None):
        captured["agent_name"] = agent_name
        captured["instructions"] = instructions
        captured["prompt"] = prompt
        captured["deployment"] = deployment
        captured["tools"] = tools
        return {"ok": True}

    monkeypatch.setattr(llm, "run_agent_json", fake_run_agent_json)

    result = llm.chat_json(
        "system instructions",
        "user prompt",
        deployment="gpt-test",
        agent_name="test-agent",
        tools=[lambda: None],
    )

    assert result == {"ok": True}
    assert captured["agent_name"] == "test-agent"
    assert captured["instructions"] == "system instructions"
    assert captured["prompt"] == "user prompt"
    assert captured["deployment"] == "gpt-test"
    assert len(captured["tools"]) == 1
