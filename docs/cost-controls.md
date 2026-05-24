# Cost Controls

The template defaults to conservative behavior.

- Azure OpenAI / Foundry model deployments are expected for useful pipeline runs.
- Structured extraction uses the chat deployment named by `AZURE_OPENAI_DEPLOYMENT`.
- Embedding-based duplicate detection uses the embedding deployment named by `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`.
- Groundedness checks use the deployment named by `AZURE_OPENAI_GROUNDEDNESS_DEPLOYMENT`.
- Source text is truncated by `llm.maxInputChars`.
- Groundedness source text is truncated by `groundedness.maxInputChars`.
- Source pages have revisit intervals.
- Candidate queues decouple discovery from extraction.
- Review gates prevent storing low-quality records.
- Application Insights should be used to monitor failures and dependencies.

## Expected Cost Shape

Costs come from two different shapes: baseline infrastructure and per-run usage.

### Baseline infrastructure

- **Cosmos DB is the main baseline cost in the current template.** The Bicep template creates each Cosmos DB container with dedicated provisioned throughput. In the smoke-test deployment this resolved to seven containers at 400 RU/s each: `SourcePageRegistry`, `CandidateQueue`, `ReviewQueue`, `Records`, `PipelineRuns`, `TokenUsage`, and `PipelineConfig`.
- At the Sweden Central retail meter observed on 2026-05-24, provisioned Cosmos DB throughput was `0.0063 CHF` per `100 RU/s-hour`. That makes the current template roughly `7 containers * 4 * 0.0063 CHF/hour`, or about `127-130 CHF/month` before storage, discounts, free tier, reservations, or regional price changes.
- Azure Storage is usually small for this pipeline unless deployment packages, logs, or retained source data grow substantially.
- Azure Functions Flex Consumption has no always-ready instances in the default template, so function compute is mostly usage-driven.
- Application Insights and Log Analytics scale with telemetry ingestion. They are usually modest at low volume, but verbose SDK traces can increase ingestion cost.
- The Azure AI Services resource itself is not the expensive part; model deployments and model calls are. For operational runs, expect chat extraction, embedding generation, and groundedness checks to contribute usage-based model cost.

For low-frequency experiments, consider adding a production-hardening pass before broad use: Cosmos DB serverless, free tier, shared database throughput, or fewer containers can materially reduce the idle baseline. The right choice depends on expected RU volume, vector search requirements, and whether predictable throughput is more important than low idle cost.

### Per-run usage

Let:

- `S` = source pages screened per run
- `L` = `sourceDiscovery.maxLinksPerSource`
- `C` = candidate URLs processed per run, up to `S * L`
- `A` = approved records per run
- `R` = runs per month

Then monthly work scales approximately as:

- **Discovery HTTP fetches:** `R * S`
- **Candidate extraction fetches:** `R * C`
- **Review source fetches:** up to `R * A`, because groundedness may fetch the source again
- **Function executions:** roughly `R * (S-triggered HTTP calls + C candidate-trigger executions + C review-trigger executions)`
- **Cosmos DB operations:** `R * (source registry writes + candidate writes + candidate reads + review writes + review reads + duplicate queries + approved record writes)`
- **LLM extraction calls:** `R * C` for the expected chat extraction path
- **Embedding calls:** `R * C` for provider-neutral duplicate detection
- **LLM groundedness calls:** up to `R * A` for groundedness review

Frequency therefore scales costs linearly until a service limit is reached. Moving from a 14-day cadence to a daily cadence is about a 14x increase in discovery, extraction, review, model calls, Cosmos operations, and logs, assuming the same seeds and link limits.

Example with `5` seed pages and `maxLinksPerSource = 25`:

- Every 14 days: about `2` runs/month, up to `250` candidates/month.
- Daily: about `30` runs/month, up to `3,750` candidates/month.
- Hourly: about `720` runs/month, up to `90,000` candidates/month, which is no longer a casual scraping workload and should have stricter domain filters, rate limits, and budget alerts.

### Model cost scaling

Model cost is usually the fastest-growing variable cost because model deployments are part of the intended pipeline.

- Chat extraction is bounded by `llm.maxInputChars` and runs once per candidate.
- Embeddings are bounded by `embedding.maxInputChars` and run once per candidate.
- LLM groundedness is bounded by `groundedness.maxInputChars` and runs once per approved record.

Lower `maxInputChars`, smaller seed lists, tighter allowed domains, and lower `maxLinksPerSource` directly reduce model tokens and total pipeline volume.

## Cost Data From The Smoke-Test Subscription

The smoke-test resource group was too new to show posted Cost Management rows at query time; Azure Cost Management often lags behind live deployment and telemetry data.

Month-to-date subscription data did show the expected cost drivers in a comparable resource group: Foundry Models, Functions, Cosmos DB, Log Analytics, Storage, and related hosting/networking services. In that sample, Foundry Models were the largest line item, followed by Functions and Cosmos DB. Treat this as a directional signal: model usage can dominate active runs, while provisioned Cosmos DB throughput is likely to dominate idle cost.

Recommended first deployment:

1. Use a small seed URL list.
2. Keep `maxLinksPerSource` between 10 and 25.
3. Configure chat, embedding, and groundedness model deployments before running the pipeline.
4. Run a small end-to-end LLM extraction and review test.
5. Review token, embedding, vector query, and function execution costs before increasing cadence.
