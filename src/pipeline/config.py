import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SchemaField(BaseModel):
    name: str
    type: Literal["string", "number", "boolean", "array", "object"] = "string"
    required: bool = False


class SchemaConfig(BaseModel):
    fields: list[SchemaField] = Field(default_factory=list)


class SourceDiscoveryConfig(BaseModel):
    seedUrls: list[str] = Field(default_factory=list)
    allowedDomains: list[str] = Field(default_factory=list)
    blockedDomains: list[str] = Field(default_factory=list)
    revisitFrequencyDays: int = 14
    maxLinksPerSource: int = 25


class LlmConfig(BaseModel):
    provider: str = "azure-openai"
    deploymentNameEnv: str = "AZURE_OPENAI_DEPLOYMENT"
    maxInputChars: int = 18000
    temperature: float = 0.1


class QualityConfig(BaseModel):
    requireSourceEvidence: bool = True
    reviewBeforeStore: bool = True
    duplicateDetection: bool = True


class PipelineConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    projectName: str = "explorative-scraping-pipeline"
    recordType: str = "record"
    domainDescription: str = "Public web records."
    sourceDiscovery: SourceDiscoveryConfig = Field(default_factory=SourceDiscoveryConfig)
    recordSchema: SchemaConfig = Field(default_factory=SchemaConfig, alias="schema")
    llm: LlmConfig = Field(default_factory=LlmConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)


@lru_cache(maxsize=1)
def load_config() -> PipelineConfig:
    path = Path(os.getenv("PIPELINE_CONFIG_PATH", "pipeline.config.json"))
    if not path.exists():
        return PipelineConfig()
    return PipelineConfig.model_validate(json.loads(path.read_text(encoding="utf-8")))
