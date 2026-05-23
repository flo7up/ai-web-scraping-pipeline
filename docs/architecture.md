# Architecture

The pipeline is an Azure Functions app with queue-driven processing.

```mermaid
flowchart LR
  Source[Source pages] --> Screen[HttpScreenSources]
  Screen --> Candidate[CandidateQueue]
  Candidate --> Extract[CosmosCandidateTrigger]
  Extract --> Review[ReviewQueue]
  Review --> Approve[CosmosReviewTrigger]
  Approve --> Records[Records]
  Records --> Search[HttpSearchRecords]
```

## Main Runtime Components

- `HttpScreenSources`: discovers candidate URLs from seed pages.
- `CosmosCandidateTrigger`: fetches candidate URLs and extracts structured records.
- `CosmosReviewTrigger`: validates extracted records and stores approved output.
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

## Configuration

Domain behavior lives in `pipeline.config.json`, not code. Use it to change schema, seed sources, source filtering, and LLM behavior.
