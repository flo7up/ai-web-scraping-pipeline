# Architecture

The pipeline is an Azure Functions app with queue-driven processing.

![AI Web Scraping Pipeline schematic](../ai-web-scraping-pipeline-overview-schematic.png)

The schematic shows the conceptual flow. The implementation uses Cosmos DB containers for queue-like handoff between agents rather than a separate Azure Queue Storage resource.

When `AZURE_AI_PROJECT_ENDPOINT` is configured, chat-style LLM calls for Discovery, Extraction, and Review are made through Microsoft Agent Framework. The discovery search functions are decorated as Agent Framework tools. Embeddings still use the Azure OpenAI-compatible embeddings API.

```mermaid
flowchart LR
  Source[Source pages] --> Screen[HttpScreenSources]
  Screen --> Candidate[CandidateQueue]
  Candidate --> Extract[CosmosCandidateTrigger]
  Extract --> Review[ReviewQueue]
  Review --> Quality[CosmosReviewTrigger quality gates]
  Quality --> Duplicate{Duplicate?}
  Duplicate -- yes --> Rejected[Review item rejected]
  Duplicate -- no --> Grounded[Groundedness check]
  Grounded --> Records[Records]
  Records --> Search[HttpSearchRecords]
```

## Main Runtime Components

Start with `src/pipeline/agents/` when reading the code. These files contain the pipeline business logic; the Azure Function files are mostly trigger adapters.

- `DiscoveryAgent` (`src/pipeline/agents/discovery_agent.py`): uses the LLM to generate search queries when needed, finds candidate URLs from curated seed pages or search providers, applies domain filters, and writes candidates to `CandidateQueue`.
- `ExtractionAgent` (`src/pipeline/agents/extraction_agent.py`): fetches each candidate page, runs LLM structured extraction, and writes review items to `ReviewQueue`.
- `ReviewAgent` (`src/pipeline/agents/review_agent.py`): validates extracted records, creates embeddings, checks duplicates, evaluates groundedness, and stores approved records in `Records`.
- `HttpScreenSources`: HTTP adapter for the discovery agent.
- `CosmosCandidateTrigger`: Cosmos DB trigger adapter for the extraction agent.
- `CosmosReviewTrigger`: Cosmos DB trigger adapter for the review agent.
- `HttpExtractUrl`: manual one-off extraction endpoint.
- `HttpSearchRecords`: simple read endpoint for approved records.
- `TimerSourceRefresh`: revisits due source pages.

## Storage

Cosmos DB containers are defined in `src/pipeline/cosmos.py`.

- `SourcePageRegistry`
- `CandidateQueue`
- `ReviewQueue`
- `Records`
- `PipelineRuns`
- `TokenUsage`

The `Records` container is deployed with a vector policy on `/embedding`. Approved records can store provider-neutral embeddings so the review stage can find semantically similar existing records with Cosmos DB `VectorDistance`.

## Quality Features

- Deduplication: exact normalized source URL/hash matches are treated as duplicates, and the intended review path creates provider-neutral embeddings with `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` so it can search existing records by vector distance.
- Duplicate signals: vector similarity is combined with title similarity, organization overlap, content overlap, and technology overlap before a record is rejected as a duplicate.
- Groundedness: approved records are checked against the fetched source text with the configured `AZURE_OPENAI_GROUNDEDNESS_DEPLOYMENT`. Results are stored on the record and review item.

## Configuration

Domain behavior lives in `pipeline.config.json`, not code. Use it to change schema, seed sources, source filtering, and LLM behavior.
