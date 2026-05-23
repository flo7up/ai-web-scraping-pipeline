import os
from functools import cache, lru_cache
from typing import Any

from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential

DEFAULT_CONTAINERS = {
    "config": ("PipelineConfig", "/PartitionKey"),
    "source_pages": ("SourcePageRegistry", "/pk"),
    "candidates": ("CandidateQueue", "/PartitionKey"),
    "review": ("ReviewQueue", "/PartitionKey"),
    "records": ("Records", "/PartitionKey"),
    "runs": ("PipelineRuns", "/PartitionKey"),
    "token_usage": ("TokenUsage", "/agentName"),
}


def _database_name() -> str:
    return os.getenv("COSMOS_DATABASE_NAME", "explorative-pipeline")


@lru_cache(maxsize=1)
def cosmos_client() -> CosmosClient:
    connection_string = os.getenv("CosmosDBConnection") or os.getenv("COSMOS_CONNECTION_STRING")
    if connection_string:
        return CosmosClient.from_connection_string(connection_string)

    endpoint = os.getenv("COSMOS_ENDPOINT")
    if not endpoint:
        raise RuntimeError("Set CosmosDBConnection or COSMOS_ENDPOINT")
    return CosmosClient(endpoint, credential=DefaultAzureCredential())


@lru_cache(maxsize=1)
def database():
    client = cosmos_client()
    return client.create_database_if_not_exists(_database_name())


@cache
def container(alias: str):
    name, partition_key = DEFAULT_CONTAINERS[alias]
    return database().create_container_if_not_exists(id=name, partition_key=PartitionKey(path=partition_key))


def upsert(alias: str, item: dict[str, Any]) -> dict[str, Any]:
    return container(alias).upsert_item(item)


def query(alias: str, query_text: str, parameters: list[dict[str, Any]] | None = None, **kwargs) -> list[dict[str, Any]]:
    return list(container(alias).query_items(query=query_text, parameters=parameters or [], **kwargs))
