import json
import os
from functools import lru_cache
from typing import Any

from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

from .framework import agent_framework_enabled, run_agent_json


@lru_cache(maxsize=1)
def azure_openai_client() -> AzureOpenAI | None:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        return None

    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        return AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=api_version)

    credential = DefaultAzureCredential()

    def token_provider() -> str:
        return credential.get_token("https://cognitiveservices.azure.com/.default").token

    return AzureOpenAI(azure_endpoint=endpoint, azure_ad_token_provider=token_provider, api_version=api_version)


def chat_json(
    system_prompt: str,
    user_prompt: str,
    deployment: str | None,
    temperature: float = 0.1,
    agent_name: str = "pipeline-agent",
    tools: list | None = None,
) -> dict[str, Any] | None:
    if not deployment:
        return None
    if agent_framework_enabled():
        return run_agent_json(agent_name, system_prompt, user_prompt, deployment, tools=tools)

    client = azure_openai_client()
    if client is None:
        return None

    response = client.chat.completions.create(
        model=deployment,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)
